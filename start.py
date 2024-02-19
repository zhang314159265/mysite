from http import server as http_server
from http import HTTPStatus
import shutil
import subprocess

class MyHTTPRequestHandler(http_server.SimpleHTTPRequestHandler):
    def serve_root(self):
        self.send_response(HTTPStatus.OK)
        self.end_headers()

        with open("index.html", "rb") as f:
            shutil.copyfileobj(f, self.wfile)

    def serve_grep(self, repo, pattern):
        self.send_response(HTTPStatus.OK)
        self.end_headers()

        if repo not in ["triton", "llvm"]:
            return self.reply(f"Unsupported repo {repo}")

        pattern = pattern.strip()
        if len(pattern) < 5 or not pattern.isidentifier():
            return self.reply(f"Unsupported pattern {pattern}")
        
        grep_out = subprocess.check_output(
            f"grep -Inr {pattern} repos/{repo}".split()).decode()

        lines = grep_out.splitlines()

        LIM = 1000
        trimed = False
        if len(lines) > LIM:
            lines = lines[:LIM]
            trimed = True

        self.reply("<html><body>\n")
        self.reply(f"<p>Response contains {len(lines)} lines</p>\n") # report number of lines after potential trimming
        file_prefix = f"repos/{repo}/"
        for line in lines:
            comps = line.split(":", 2)
            assert len(comps) == 3
            file, lno, matched_line = comps
            assert file.startswith(file_prefix) 
            file = file[len(file_prefix):]
            others = matched_line.split(pattern)
            rendered_matched_line = f"<span style='color:red;'>{pattern}</span>".join(others)
            self.reply(f"<p><span style='background-color:DodgerBlue;'>{file}</span>:{lno}: {rendered_matched_line}</p>\n")
        if trimed:
            self.reply("<p>......</p>\n")
        self.reply("</body></html>\n")

    def notify_get_not_implemented(self):
        self.send_response(HTTPStatus.OK)
        self.end_headers()

        self.reply(f"GET {self.path} is not implemented\n")

    def reply(self, message):
        if isinstance(message, str):
            message = message.encode()
        self.wfile.write(message)

    def parse_path_and_query_string(self, path_and_query_string):
        comps = path_and_query_string.split("?")
        if len(comps) == 1:
            return comps[0], None
        assert len(comps) == 2
        path, query_string = comps

        comps = query_string.split('&')
        query_args = {}
        for comp in comps:
            key, val = comp.split('=')
            query_args[key] = val
        return path, query_args

    def do_GET(self):
        path, query_args = self.parse_path_and_query_string(self.path)
        if path == '/':
            self.serve_root()
        elif path == "/grep":
            self.serve_grep(**query_args)
        else:
            self.notify_get_not_implemented()

    def do_HEAD(self):
        raise NotImplementedError

def main():
    http_server.test(MyHTTPRequestHandler, port=8080)

if __name__ == "__main__":
    main()
    print("bye")
