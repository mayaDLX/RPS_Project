import asyncio
import web_stream

if __name__ == '__main__':
    server = web_stream.WebSocketServer()
    asyncio.run(server.run())
