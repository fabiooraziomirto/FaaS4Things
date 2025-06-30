def handler(context, event):
    context.logger.info('Reading file.txt...')

    try:
        with open("file.txt", "r") as f:
            content = f.read()
    except Exception as e:
        error_msg = f"Errore durante la lettura del file: {str(e)}"
        context.logger.error(error_msg)
        return context.Response(body=error_msg,
                                headers={},
                                content_type='text/plain',
                                status_code=500)

    return context.Response(body=content,
                            headers={},
                            content_type='text/plain',
                            status_code=200)
