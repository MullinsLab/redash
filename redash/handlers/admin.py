import json
from flask import current_app

from redash.wsgi import app
from redash import models, redis_connection
from redash.utils import json_dumps
from redash.permissions import require_super_admin
from redash.tasks.queries import QueryTaskTracker


def json_response(response):
    return current_app.response_class(json_dumps(response), mimetype='application/json')


@app.route('/api/admin/queries/outdated')
@require_super_admin
def outdated_queries():
    manager_status = redis_connection.hgetall('redash:status')
    query_ids = json.loads(manager_status.get('query_ids', '[]'))
    if query_ids:
        outdated_queries = models.Query.select(models.Query, models.QueryResult.retrieved_at, models.QueryResult.runtime) \
            .join(models.QueryResult, join_type=models.peewee.JOIN_LEFT_OUTER) \
            .where(models.Query.id << query_ids) \
            .order_by(models.Query.created_at.desc())
    else:
        outdated_queries = []

    print outdated_queries

    return json_response(dict(queries=[q.to_dict(with_stats=True, with_last_modified_by=False) for q in outdated_queries], updated_at=manager_status['last_refresh_at']))


@app.route('/api/admin/queries/tasks')
@require_super_admin
def queries_tasks():
    waiting = QueryTaskTracker.all(QueryTaskTracker.WAITING_LIST)
    in_progress = QueryTaskTracker.all(QueryTaskTracker.IN_PROGRESS_LIST)
    done = QueryTaskTracker.all(QueryTaskTracker.DONE_LIST, limit=50)

    response = {
        'waiting': [t.data for t in waiting],
        'in_progress': [t.data for t in in_progress],
        'done': [t.data for t in done]
    }

    return json_response(response)




