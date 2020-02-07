"""
Entry file for the delayed jobs app
"""
from flask import Flask, Blueprint

from app.config import RUN_CONFIG
from app.config import RunEnvs
from app.db import DB



def create_app():
    """
    Creates the flask app
    :return: Delayed jobs flask app
    """

    flask_app = Flask(__name__)
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = RUN_CONFIG.get('sql_alchemy').get('database_uri')
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = RUN_CONFIG.get('sql_alchemy').get('track_modifications')
    flask_app.config['SECRET_KEY'] = RUN_CONFIG.get('server_secret_key')

    authorizations = {
        'jobKey': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-Job-Key'
        },
        'adminKey': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-Admin-Key'
        }
    }

    with flask_app.app_context():
        DB.init_app(flask_app)

        create_tables = RUN_CONFIG.get('sql_alchemy').get('create_tables', False)
        if create_tables:
            DB.create_all()

        base_path = RUN_CONFIG.get('base_path', '')

        swager_desc_blueprint = Blueprint('swagger', __name__, url_prefix=f'{base_path}/swagger')

        @swager_desc_blueprint.route('/swagger.json')
        def get_json():
            from flask import jsonify
            return jsonify({'hello': 'world'})

        flask_app.register_blueprint(swager_desc_blueprint)



        # api = Api(
        #     title='ChEMBL Interface Delayed Jobs',
        #     version='1.0',
        #     description='A microservice that runs delayed jobs for the ChEMBL interface. '
        #                 'For example generating a .csv file from elasticsearch',
        #     app=blueprint,
        #     authorizations=authorizations,
        # )
        #
        # flask_app.register_blueprint(blueprint)
        #
        # for namespace in [job_admin_namespace, job_status_namespace, submit_test_job_namespace,
        #                   submit_similarity_search_namespace, submit_substructure_search_namespace,
        #                   submit_connectivity_search_namespace, submit_blast_search_namespace, record_search_namespace,
        #                   record_download_namespace, submit_download_namespace]:
        #     api.add_namespace(namespace)

        return flask_app

if __name__ == '__main__':
    flask_app = create_app()
