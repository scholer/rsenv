"""



"""

import re
import time
import zipfile
from urllib.parse import urlparse
from io import BytesIO
import requests


zipfnfmt = "{jobid}/{T:0.01f}/{jobid}{output}"  # t_* files are just thumbnails
TOKEN_REGEX = re.compile(r"token=(\w+)")


def token_from_url(url):
    match = TOKEN_REGEX.search(url)
    token = match.group(1) if match else None
    return token


def jobid_from_url(url):
    url_parts = urlparse(url)
    job_id = url_parts.path.strip("/").split('/')[-1]
    try:
        return int(job_id)
    except ValueError:
        return None


def nupack_job_outputfn(jobid, T, typ, key, oidx=None, plotenum=0, ext='png'):
    """
    >>> nupack_job_outputfn(typ="cx")

    """
    if typ == 'data' and key != 'dp':
        if oidx is None:
            assert key in ('cx', 'fpairs', 'label')
            output = ".%s" % key
        else:
            assert key in ('in', 'label', 'mfe', 'ppairs')  # Only these types of data available when specifying oidx
            output = "_%s.%s" % (oidx, key)
    else:
        assert typ == 'plot' or key == 'dp'
        if key == 'dp' and typ == 'data':
            ext = 'dat'
        if oidx is None:
            assert key == 'dp'  # only supported output for (typ='plot' and oidx=None)
            output = "_summary_%s.%s" % (key, ext)
        else:
            output = "_%s_%s_%s.%s" % (oidx, plotenum, key, ext)
    return zipfnfmt.format(jobid=jobid, T=T, output=output)


def get_complex_filedata(job, jobid, key='in', T=37, oidx=0):
    fn = nupack_job_outputfn(jobid=jobid, T=T, typ='data', key=key, oidx=oidx)

    if isinstance(job, requests.Response):
        jobfile = BytesIO(job.content)
    elif isinstance(job, (bytes, bytearray)):
        jobfile = BytesIO(job)
    else:
        print("Opening zip file:", job)
        jobfile = job

    with zipfile.ZipFile(jobfile) as zip_fd:
        assert zip_fd.testzip() is None  # None = "OK"
        print("archive filename:", fn)
        indata = zip_fd.read(fn).decode('utf8')

    return indata


def get_complex_structure_dotparens(job, jobid, T=37, oidx=0):
    indata = get_complex_filedata(job, jobid, T=T, oidx=oidx, key='in')
    return indata.split('\n')[1]


def parse_mfe_data(data):
    data = (line.strip() for line in data.split('\n'))
    data = (line for line in data if line and line[0] != "%")
    nbases = int(next(data))
    mfe_dg = float(next(data))
    dotparens = next(data)
    assert nbases == len(dotparens)
    pairs = [[int(v) for v in line.split()] for line in data]
    pairmap = dict(pairs)
    pairmap.update({v: k for k, v in pairmap.items()})
    return {
        'nbases': nbases,
        'mfe_dG': mfe_dg,
        'dotparens': dotparens,
        'mfe_pairs': pairs,
        'mfe_pairmap': pairmap
    }


def parse_ppairs_data(data):
    data = (line.strip() for line in data.split('\n'))
    data = (line for line in data if line and line[0] != "%")
    nbases = int(next(data))
    pairs = [(int(b1), int(b2), float(p)) for b1, b2, p in [line.split() for line in data]]
    pairprob = {}
    for b1, b2, prob in pairs:
        pairprob[(b1, b2)] = prob
        pairprob[(b2, b1)] = prob
    return {
        'nbases': nbases,
        'ppairs': pairs,
        'pairprob': pairprob
    }


def get_complex_structure_info(job, jobid, T=37, oidx=0):
    mfedata = get_complex_filedata(job, jobid, T=T, oidx=oidx, key='mfe')
    mfeinfo = parse_mfe_data(mfedata)
    ppairsdata = get_complex_filedata(job, jobid, T=T, oidx=oidx, key='ppairs')
    ppairsinfo = parse_ppairs_data(ppairsdata)
    assert mfeinfo['nbases'] == ppairsinfo['nbases']
    nbases = mfeinfo['nbases']
    # dotparens_pairs = mfeinfo['pairs']
    pairprob = ppairsinfo['pairprob']  # {(b1, b2): prob}
    pairmap = mfeinfo['mfe_pairmap']  # obs: NuPack uses 1-based indexing for bases
    dotparens_prob = [0]*nbases
    # print("\npairmap:", pairmap)
    for i in range(nbases):
        b1 = i + 1
        if b1 in pairmap:
            b2 = pairmap[b1]
            dotparens_prob[i] = pairprob[(b1, b2)]

    dotparens_prob_0to9 = [int(v*10 - 1e-3) if v > 0.01 else 0 for v in dotparens_prob]
    assert set(dotparens_prob_0to9) <= set(range(10))  # same as set.issubset()
    mfeinfo.update(ppairsinfo)
    mfeinfo['dotparens_prob'] = dotparens_prob  # mfe_pair_prob
    mfeinfo['dotparens_prob_0to9'] = dotparens_prob_0to9  # mfe_pair_prob_digit  # single digit (0-9) scale
    return mfeinfo


def get_job_status(job):
    if isinstance(job, str):
        # job is URL:
        jobid = jobid_from_url(job)
        token = token_from_url(job)
        job = dict(jobid=jobid, token=token)
    uri_fmt = "http://nupack.org/partition/check_results/{jobid}?token={token}"
    uri = uri_fmt.format(**job)
    probe = requests.get(uri)
    return probe


def is_job_done(job):
    probe = get_job_status(job)
    probe.raise_for_status()
    return "stop_checking_results = true" in probe.text


def wait_until_done(job, sleep=2, wait_max=60, print_dots=True, raise_err=False):
    """Returns True when job is done. Returns None if wait time exceeded wait_max."""
    wait_total = 0
    while wait_total < wait_max:
        if is_job_done(job):
            return True
        if print_dots:
            print(".", end="")
        wait_total += sleep
        time.sleep(sleep)
    if raise_err:
        raise RuntimeWarning("Waited longer than wait_max, aborting...")
    elif print_dots:
        print("Waited longer than wait_max, aborting...")
