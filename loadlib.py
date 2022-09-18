if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    import sys


    def test_connection():
        import requests
        res = requests.get("http://www.google.com", timeout=10)
        if res.status_code == 200:
            return True
        return False
    if not test_connection():
        sys.exit()
    from src import main

    main.MainApp().run()