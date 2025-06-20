from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime
import os


class base_case(object):
    '''Parent for case handlers.'''

    def handle_file(self, handler, full_path):
        try:
            with open(full_path, 'rb') as reader:
                content = reader.read()
            handler.send_content(content)
        except IOError as msg:
            msg = "'{0}' cannot be read: {1}".format(full_path, msg)
            handler.handle_error(msg)
    
    def index_path(self, handler):
        return os.path.join(handler.full_path, 'index.html')
    
    def test(self, handler):
        assert False, 'Not implemented.'

    def act(self, handler):
        assert False, 'Not implemented.'

class case_cgi_file(object):
    '''Something runnable.'''
    def test(self, handler):
        return os.path.isfile(handler.full_path) and \
               handler.full_path.endswith('.py')
    
    def act(self, handler):
        handler.run_cgi(handler.full_path)

    def run_cgi(self, full_path):
        cmd = "python " + full_path
        child_stdin, child_stdout = os.popen2(cmd)
        child_stdin.close()
        data = child_stdout.read()
        child_stdout.close()
        self.send_content(data)

class case_no_file(object):
    '''File or directory does not exist.'''
    def test(self, handler):
        return not os.path.exists(handler.full_path)
    
    def act(self, handler):
        raise ServerException("'{0}' not found".format(handler.path))
        
class case_existing_file(base_case):
    '''File exists.'''
    def test(self, handler):
        return os.path.isfile(handler.full_path)
   
    def act(self, handler):
        self.handle_file(handler, handler.full_path)

class case_always_fail(object):
    '''Base case if nothing else worked.'''

    def test(self, handler):
        # 返回True，表示该case总是失败
        return True
    
    def act(self, handler):
        # 抛出ServerException异常，表示未知对象
        raise ServerException("Unknown object '{0}'".format(handler.path))

class case_directory_index_file(object):
    '''Serve index.html page for a directory.'''
    def index_path(self, handler):
        return os.path.join(handler.full_path, 'index.html')
    
    def test(self, handler):
        return os.path.isdir(handler.full_path) and \
               os.path.isfile(self.index_path(handler))
    
    def act(self, handler):
        handler.handle_file(self.index_path(handler))

class case_directory_no_index_file(object):
    '''Serve listing for a directory without an index.html page.'''

    def index_path(self, handler):
        return os.path.join(handler.full_path, 'index.html')
    
    def test(self, handler):
        return os.path.isdir(handler.full_path) and \
               not os.path.isfile(self.index_path(handler))
    
    def act(self, handler):
        handler.list_dir(handler.full_path)


class ServerException(Exception):
    """服务器处理请求时发生的错误"""
    pass

class RequestHandler(BaseHTTPRequestHandler):
    '''Handle HTTP requests by returning a fixed 'page'.'''

    Cases = [case_no_file(), 
             case_cgi_file(),
             case_existing_file(),
             case_directory_index_file(), 
             case_directory_no_index_file(),
             case_always_fail()]

    
    # How to display an error.
    Error_Page = """\
        <html>
        <body>
        <h1>Error accessing {path}</h1>
        <p>{msg}</p>
        </body>
        </html>
        """

    # Page to send back.
    Page = '''\
<html>
<body>
<table>
<tr>    <td>Header</td>            <td>Value</td>         </tr>
<tr>    <td>Date and time</td>     <td>{date_time}</td>   </tr>
<tr>    <td>Client host</td>       <td>{client_host}</td> </tr>
<tr>    <td>Client port</td>       <td>{client_port}</td> </tr>
<tr>    <td>Command</td>           <td>{command}</td>     </tr>
<tr>    <td>Path</td>              <td>{path}</td>        </tr>
</table>
</body>
</html>
'''

    # How to disaplay a directory listing.
    Listing_Page = '''\
        <html>
        <body>
        <ul>
        {0}
        </ul>
        </body>
        </html>
        '''
    
    # Handle a GET request.
    def do_GET(self):
        try:

            # Figure out what exactly is being requested.
            self.full_path = os.getcwd() + self.path

            # Figure out how to handle it.
            for case in self.Cases:
                if case.test(self):
                    case.act(self)
                    break

        # 出错处理
        except Exception as msg:
            self.handle_error(msg)

    def handle_file(self, full_path):
        try:
            with open(full_path, 'rb') as reader:
                content = reader.read()
            self.send_content(content)
        except IOError as msg:
            msg = "'{0}' cannot be read: {1}".format(self.path, msg)
            self.handle_error(msg)    

    def handle_error(self, msg):
        content = self.Error_Page.format(path=self.path, msg=msg)
        self.send_content(content, 404)

    # Send actual content.
    def send_content(self, content, status=200):
        if isinstance(content, str):
            content = content.encode('utf-8')  # 确保是字节类型
        self.send_response(status)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)



if __name__ == '__main__':
    serverAddress = ('', 8080)
    server = HTTPServer(serverAddress, RequestHandler)
    server.serve_forever()


