import click


class BaseClickCommand(click.Command):
    pass
    ## Commented out because now the disconnection from TWS is done in
    ##  tws_api_client module's atexit
    # from click import Context
    # def invoke(self, ctx: Context) -> Any:
    #     try:
    #         result = super().invoke(ctx)
    #     finally:
    #         from ..clients.tws_api_client import disconnect
    #         disconnect()
    #     return result
