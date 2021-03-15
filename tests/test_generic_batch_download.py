# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""



## How to mock requests.Session.get() calls?


* Option 1: Ad-hoc mocking of the requests library.
* Option 2: Use a general mocking library, e.g. `mock`.
* Option 3: Use a requests-specific mocking package.


### Option 1: Ad-hoc mocking

This is pretty easy in Python, just replace the class's `.get()` method, as outlined below.
However, this has the obvious side-effect of altering the requests library globally for
the entire interpreter session. If you have anything that expects requests to be available,
that will obviously prevent that.

```
import requests

MOCK_RESPONSE = requests.Response()
MOCK_RESPONSE.status_code = 200
MOCK_RESPONSE._content = b"mocked content"

def mock_get(self, url, *args, **kwargs):
    r = requests.Response()
    r.status_code = 200
    r._content = b"mocked content for url: " + url.encode("UTF-8")
    return r

requests.Session.get = mock_get
# Now you can test functions that calls requests.Session.get()
```


### Option 2: Using a general mocking library:

This has the advantage of making it easy to "revert" mocked changes so the changes are
isolated and only apply for the required test.

```
from unittest import mock

# Use mock.patch as a decorator on your test-function:
@mock.patch('requests.Session.get', return_value=MOCK_RESPONSE)
def test_function_that_calls_requests():
    pass

# Use mock.patch as a context handler inside your test-function:
with mock.patch('requests.Session.get', return_value=MOCK_RESPONSE):
    pass

# mock.patch takes a string that matches the thing you want to mock.
# If you are mocking an existing variable (an object, including classes and modules), use mock.patch.object.
session = requests.Session
with mock.patch.object(session, 'get', return_value=MOCK_RESPONSE):
    pass
with mock.patch(requests, 'get', return_value=MOCK_RESPONSE):
    pass

```




### Option 3: Requests-specific mocking packages:

* requests-mock package
    https://requests-mock.readthedocs.io/
*

"""
