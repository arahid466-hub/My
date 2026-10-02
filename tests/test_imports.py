def test_imports():
 import engine.core
 from server.main import app
 from workers.worker import app as worker_app
 assert app.title == 'Aether AI Engine'
 assert worker_app.title == 'Aether GPU Worker'
