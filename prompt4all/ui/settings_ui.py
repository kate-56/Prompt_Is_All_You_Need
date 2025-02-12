import os

import gradio as gr
from prompt4all import context
from prompt4all.context import *
from prompt4all.utils.database_utils import parse_connection_string
from prompt4all.tools.database_tools import *
from prompt4all.utils.io_utils import process_file
import pyodbc

cxt = context._context()
driver = sorted(pyodbc.drivers())
__all__ = ['database_query_panel']


def database_query_panel():
    db_state = gr.State()

    def enable_dbquery(is_enabled):
        # tb_server_name.interactive = is_enabled
        # cb_trusted_connection.interactive = is_enabled
        # tb_user_name, tb_password.interactive = is_enabled
        # tb_database_name.interactive = is_enabled
        # tb_driver_name.interactive = is_enabled
        cxt.is_db_enable = is_enabled
        cxt.baseChatGpt.enable_database_query(is_enabled)

    def get_conn_string(server_name, trusted_connection, user_name, password, database_name, driver_name):
        conn_string = ''
        if trusted_connection:
            conn_string = 'mssql+pyodbc://@{server_name}/{database_name}?trusted_connection={trusted_connection}&driver={driver_name}'
        else:
            conn_string = 'mssql+pyodbc://{user_name}:{password}@{server_name}/{database_name}?driver={driver_name}'
        cxt.conn_string = conn_string
        return conn_string

    conn_dict = parse_connection_string(cxt.conn_string)
    cb_db_enable = gr.Checkbox(value=cxt.is_db_enable, label="是否啟用資料庫查詢")
    cb_db_enable.change(fn=enable_dbquery, inputs=[cb_db_enable], outputs=[])
    with gr.Group('資料庫設定') as conn_setting:
        tb_driver_name = gr.Textbox(interactive=True, value=conn_dict.get('driver', 'master'), label="資料提供者名稱")
        with gr.Row():
            tb_server_name = gr.Textbox(interactive=True, value=conn_dict.get('server_name', '.'), min_width=160,
                                        label="伺服器名稱")
            cb_trusted_connection = gr.Checkbox(interactive=True,
                                                value=bool(conn_dict.get('trusted_connection', 'True')), min_width=160,
                                                label="是否trusted_connection")
        with gr.Row():
            tb_user_name = gr.Textbox(interactive=True, visible=cb_trusted_connection.value, min_width=220,
                                      value=conn_dict.get('user_name', ''), label="帳號")
            tb_password = gr.Textbox(interactive=True, visible=cb_trusted_connection.value, min_width=220,
                                     value=conn_dict.get('password', ''), type='password', label="密碼")
        tb_database_name = gr.Textbox(interactive=True, value=conn_dict.get('database_name', 'master'),
                                      label="資料庫名稱")
        text_conn = gr.Textbox(interactive=False, value=cxt.conn_string, label="連線字串")

        tb_driver_name.change(get_conn_string,
                              [tb_server_name, cb_trusted_connection, tb_user_name, tb_password, tb_database_name,
                               tb_driver_name], [text_conn])

        tb_server_name.change(get_conn_string,
                              [tb_server_name, cb_trusted_connection, tb_user_name, tb_password, tb_database_name,
                               tb_driver_name], [text_conn])

        cb_trusted_connection.change(get_conn_string, [tb_server_name, cb_trusted_connection, tb_user_name, tb_password,
                                                       tb_database_name, tb_driver_name], [text_conn])

        tb_user_name.change(get_conn_string,
                            [tb_server_name, cb_trusted_connection, tb_user_name, tb_password, tb_database_name,
                             tb_driver_name], [text_conn])

        tb_password.change(get_conn_string,
                           [tb_server_name, cb_trusted_connection, tb_user_name, tb_password, tb_database_name,
                            tb_driver_name], [text_conn])

        tb_database_name.change(get_conn_string,
                                [tb_server_name, cb_trusted_connection, tb_user_name, tb_password, tb_database_name,
                                 tb_driver_name], [text_conn])

    # def set_visible(is_enable):
    #     conn_setting.visible=is_enable
    #
    # cb_db_enable.change(fn=set_visible,inputs=[cb_db_enable], outputs=[])

    schema_file = gr.File(value='examples/query_database/schema.txt', file_count="single",
                          label='請將檔案拖曳至此或是點擊後上傳',
                          file_types=[".txt", ".json", ".sql"])
    text_db_schema = gr.TextArea(interactive=False, value=cxt.databse_schema, label="資料庫Schema文件")

    schema_file.change(process_file, [schema_file, db_state], [text_db_schema, db_state])
    _panel = gr.Group(cb_db_enable, conn_setting, text_conn, schema_file, text_db_schema, elem_id="db_setting_panel")
    return _panel


def service_type_panel():
    _service_radio = gr.Radio(choices=["openai", "azure"], value=None, label="服務提供者", interactive=True)
    _secret = gr.Textbox(label="API金鑰", value="", type="text", interactive=False)
    _deployments = gr.DataFrame(headers=["deployment_endpoint", "model_name"], wrap=True, col_count=(2, 'fixed'),
                                row_count=(1, 'dynamic'), interactive=True, type="array", datatype=['str', 'str'])
    _panel = gr.Group(_service_radio, _secret, _deployments, elem_id="service_type_panel")

    def service_type_change(_service_type):
        cxt.service_type = _service_type
        api_type = "OPENAI_API_KEY"
        if _service_type == "openai":
            secret_kety = os.getenv("OPENAI_API_KEY")
        else:
            secret_kety = os.getenv("AZURE_OPENAI_API_KEY")
            api_type = "AZURE_OPENAI_API_KEY"

        if secret_kety:
            return gr.Textbox(label="API金鑰(環境變數{0})".format(api_type),
                              value=secret_kety[:3] + ''.join(['*'] * len(secret_kety[3:])), type="text",
                              interactive=False)
        else:
            return gr.Textbox(label="API金鑰(環境變數{0})".format(api_type), value="未正確設定", type="text",
                              interactive=False)

    def deployments_change(_deployments):
        if _deployments is not None:
            cxt.deployments = _deployments

    _service_radio.change(fn=service_type_change, inputs=[_service_radio], outputs=[_secret], queue=False)
    _deployments.change(deployments_change, inputs=[_deployments], outputs=[])

    _service_radio.value = cxt.service_type
    _deployments.value['data'] = cxt.deployments

    # if cxt.service_type == "azure":
    #     _secret = service_type_change("azure")
    # else:
    #     _secret = service_type_change("openai")

    return _panel
