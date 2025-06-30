def handler(context, event):
    context.logger.info('Eseguendo lettura O(n²)...')

    try:
        # Lettura iniziale per determinare la dimensione del file (n)
        with open("file.txt", "r") as f:
            content = f.read()
        n = len(content)
    except Exception as e:
        error_msg = f"Errore durante la lettura iniziale del file: {str(e)}"
        context.logger.error(error_msg)
        return context.Response(body=error_msg,
                                headers={},
                                content_type='text/plain',
                                status_code=500)

    # Lettura O(n²): leggiamo il file n volte
    try:
        last_read = ""
        for i in range(n):
            with open("file.txt", "r") as f:
                last_read = f.read()
    except Exception as e:
        error_msg = f"Errore durante le letture ripetute: {str(e)}"
        context.logger.error(error_msg)
        return context.Response(body=error_msg,
                                headers={},
                                content_type='text/plain',
                                status_code=500)

    context.logger.info(f"Letto file.txt {n} volte (simulazione O(n²))")
    return context.Response(body=last_read,
                            headers={},
                            content_type='text/plain',
                            status_code=200)
