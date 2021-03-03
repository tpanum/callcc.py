import importlib
import inspect
import io
import sys
import threading
import time

import grpc
import interpreter_pb2 as inter
import interpreter_pb2_grpc as rpc


def wrap(function_ref):
    module_name = dict(inspect.getmembers(function_ref))["__globals__"][
        "__file__"
    ].split("/")[-1][:-3]
    function_name = function_ref.__name__

    def fn(*args, **kwargs):
        channel = grpc.insecure_channel("localhost:8121")
        conn = rpc.IntepreterStub(channel)

        c = inter.Call()
        c.module = module_name
        c.method = function_name

        for output in conn.Interpret(c):
            print(output.stdout.decode("utf-8").rstrip("\n"))

        return

    fn.__wrapped__ = function_ref

    return fn


class Server(rpc.IntepreterServicer):
    def Interpret(self, request, context):
        mod = importlib.import_module(request.module)
        mod = importlib.reload(mod)
        met = getattr(mod, request.method)
        met = inspect.unwrap(met)

        b_o = io.StringIO()
        b_e = io.StringIO()

        _stdout = sys.stdout
        _stderr = sys.stderr
        sys.stdout = b_o
        sys.stderr = b_e
        last_value_stdout = 0
        last_value_stderr = 0

        t = threading.Thread(target=met)
        t.start()

        is_alive = t.isAlive if hasattr(t, "isAlive") else t.is_alive
        while is_alive():
            o = b_o.getvalue()[last_value_stdout:]
            e = b_e.getvalue()[last_value_stderr:]
            o_n = len(o)
            e_n = len(o)

            last_value_stdout += o_n
            last_value_stderr += e_n

            response = inter.Output()
            if (o_n > 0) or (e_n > 0):
                response = inter.Output()
                response.stdout = o.encode("utf-8")
                response.stderr = e.encode("utf-8")

                yield response

            time.sleep(0.02)

        t.join()
        sys.stdout = _stdout
        sys.stderr = _stderr

        o = b_o.getvalue()[last_value_stdout:]
        e = b_e.getvalue()[last_value_stderr:]
        o_n = len(o)
        e_n = len(o)

        response = inter.Output()
        if (o_n > 0) or (e_n > 0):
            response = inter.Output()
            response.stdout = o.encode("utf-8")
            response.stderr = e.encode("utf-8")

            yield response

        b_o.truncate(0)
        b_e.truncate(0)


def run(port=8121):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    rpc.add_IntepreterServicer_to_server(Server(), server)
    server.add_insecure_port("[::]:" + str(port))
    server.start()

    while True:
        time.sleep(64 * 64 * 100)
