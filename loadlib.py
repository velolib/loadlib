if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()


    def test_connection():
        import requests
        try:
            res = requests.get("http://www.google.com")
            if res.status_code == 200:
                return True
        except:
            return False
        return False
    if not test_connection():
        exit()
    from src import main

    main.MainApp().run()