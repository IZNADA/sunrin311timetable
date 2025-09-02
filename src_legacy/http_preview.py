import http.server, socketserver, os
PORT = 8080
os.chdir("out")
with socketserver.TCPServer(("0.0.0.0", PORT), http.server.SimpleHTTPRequestHandler) as httpd:
    print(f"Serving ./out at http://0.0.0.0:{PORT}")
    httpd.serve_forever()
