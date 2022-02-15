import os.path
import sys
import atexit
import select
from multiprocessing import Process, set_start_method

try:
    import subprocess32 as subprocess
except ImportError:
    import subprocess


def start_elasticsearch(
    datadir="/tmp/genomic-server",
    host="127.0.0.1",
    port=9201,
    prefix="",
    conf="./utils/dev_server/conf",
    echo=False,
):
    args = [
        os.path.join(prefix, "elasticsearch"),
        "-Enetwork.host=%s" % host,
        "-Ehttp.port=%d" % port,
        "-Epath.data=%s" % os.path.join(datadir, "data"),
        "-Epath.logs=%s" % os.path.join(datadir, "logs"),
        "-Epath.conf=%s" % conf,
    ]

    print(args)

    process = subprocess.Popen(
        args,
        close_fds=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    SUCCESS_LINE = b"started\n"

    lines = []
    for line in iter(process.stdout.readline, b""):
        if echo:
            sys.stdout.write(line.decode("utf-8"))
        lines.append(line)
        if line.endswith(SUCCESS_LINE):
            print("detected start, broke")
            break
    else:
        code = process.wait()
        msg = ("Process return code: %d\n" % code) + b"".join(lines).decode("utf-8")
        raise Exception(msg)

    if not echo:
        process.stdout.close()
    print("returning process")
    return process


def main():
    set_start_method("fork")
    processes = [start_elasticsearch(echo=True)]

    print_processes = []

    @atexit.register
    def cleanup_process():
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                for line in process.stdout:
                    sys.stdout.write(line.decode("utf-8"))
            except IOError:
                pass
            process.wait()
        for p in print_processes:
            p.terminate()

    stdouts = [p.stdout for p in processes]

    def print_to_terminal(stdout):
        while True:
            for line in iter(stdout.readline, b""):
                sys.stdout.write(line.decode("utf-8"))

    readable, writable, err = select.select(stdouts, [], stdouts, 5)
    for stdout in readable:
        print_processes.append(Process(target=print_to_terminal, args=(stdout,)))
    for stdout in err:
        print_processes.append(Process(target=print_to_terminal, args=(stdout,)))
    for p in print_processes:
        p.start()

    print("Dev-server started! ^C to exit. Happy developing!")


if __name__ == "__main__":
    main()
