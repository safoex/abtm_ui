from abtm.abtm_app import ABTMApp
import time

if __name__ == '__main__':
    app = ABTMApp()

    app.setup_all()

    time.sleep(0.1)
    app.request_tree()

    app.run()
