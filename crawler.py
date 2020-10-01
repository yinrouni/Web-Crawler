import re
import socket
import traceback
from queue import Queue
import sys

HOST = 'cs5700fa20.ccs.neu.edu'  # Server hostname or IP address
PORT = 80  # Port
urls = set()
frontier = Queue()
visited = set()


def generaterHeader(method, path, cookie, data):
    if method == 'POST':
        prefix = "%s %s HTTP/1.1\r\nHost: %s\r\nContent-Type: application/x-www-form-urlencoded" \
                 "\r\nContent-Length: %s\r\n" % (method, path, HOST, len(data))
    else:
        prefix = "%s %s HTTP/1.1\r\nHost: %s\r\n" % (method, path, HOST)

    if cookie and data:
        return ("%sCookie: %s\r\n\r\n%s" % (prefix, cookie, data)).encode()
    elif not data and cookie:
        return ("%sCookie: %s\r\n\r\n" % (prefix, cookie)).encode()

    elif data and not cookie:
        return ("%s\r\n%s" % (prefix, data)).encode()

    return ("%s\r\n" % prefix).encode()


def getCookie():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (socket.gethostbyname(HOST), PORT)

    try:
        client_socket.connect(server_address)

        request_header = generaterHeader("GET", '/accounts/login/?next=/fakebook/', None, None)
        client_socket.sendall(request_header)

        response = []
        while True:
            recv = client_socket.recv(2048)
            if not recv:
                break
            response = recv.decode().split('\r\n\r\n')

        csrfToken = re.findall('csrftoken=[^;]*;', response[0])[0]
        sessionId = re.findall('sessionid=[^;]*;', response[0])[0]

        # print(csrfToken)
        # print(sessionId)
        return csrfToken + sessionId
    except Exception:
        print(traceback.format_exc())

    finally:
        client_socket.close()


def login(cookie):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (socket.gethostbyname(HOST), PORT)
    try:
        client_socket.connect(server_address)

        # TODO: replace credentials
        request_header = generaterHeader("POST", '/accounts/login/', cookie,
                                         'username=001445026&password=JHXZX0UI&next=%2Ffakebook%2F&csrfmiddlewaretoken=' +
                                         cookie.split(";")[0].split('=')[1])
        client_socket.sendall(request_header)

        response = []
        while True:
            recv = client_socket.recv(2048)
            if not recv:
                continue
            response = recv.decode().split('\r\n\r\n')
            break

        cookie = renewCookie(cookie, response[0])
        frontier.put('/fakebook/')
        urls.add('/fakebook/')
        return cookie
    except Exception:
        print(traceback.format_exc())

    finally:
        client_socket.close()

        # login_header = generaterHeader("GET", "/fakebook/", cookie, None)
        #
        # client_socket.sendall(login_header)
        # while True:
        #     recv = client_socket.recv(2048)
        #
        #     if not recv:
        #         continue
        #     response = recv.decode().split('\r\n\r\n')
        #
        #     break
        # print(response[0])
        # print(response[1])
        # return response



def crawl(cookie):
    if frontier.empty():
        return

    path = frontier.get()
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (socket.gethostbyname(HOST), PORT)
    response = []

    try:
        client_socket.connect(server_address)
        header = generaterHeader("GET", path, cookie, None)

        client_socket.sendall(header)
        while True:
            recv = client_socket.recv(2048)

            if not recv:
                continue
            response = recv.decode().split('\r\n\r\n')
            break
    except Exception:
        traceback.format_exc()
    finally:
        client_socket.close()

        if len(response)== 0:
            return response
        # print(response[0])
        # print(response[1])

        links = re.findall('<a href="(/[^>]+)">',response[1])
        getSecret(response[1])
        for path in links:
            if path in urls:
                continue
            frontier.put(path)
            urls.add(path)
            print(path)
            crawl(cookie)

        return response





    # links = re.findall('<a href="(/[^>]+)">', html)
    # getSecret(html)
    # for path in links:
    #     print(path)
    #     if (path in urls) or (path in visited):
    #         continue
    #     frontier.put(path)


    # client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # server_address = (socket.gethostbyname(HOST), PORT)
    #
    # try:
    #     client_socket.connect(server_address)
    #
    # except Exception:
    #     traceback.format_exc()
    # finally:
    #     client_socket.close()


def renewCookie(cookie, header):
    sessionId = re.findall('sessionid=[^;]*;', header)[0]
    tmp = cookie.split(";")
    tmp[1] = sessionId[:-1]
    return ';'.join(tmp)


def getSecret(content):
    for secret in re.findall('<h2 class=\'secret_flag\' style="color:red">(.+)</h2>', content):
        print(secret)

sys.setrecursionlimit(3000)
cookie = getCookie()
if cookie:
    print(cookie)
    cookie = login(cookie)
    print(cookie)
    crawl(cookie)


