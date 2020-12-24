from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import datetime
import redis
import json
import uuid

redis_client = redis.Redis(host='localhost', port=6379,
                           db=0, decode_responses=True)
pubsub_client = redis_client.pubsub(ignore_subscribe_messages=True)


@require_http_methods(["POST"])
def initialize_crawl(request):

    url = json.loads(request.body).get("url")
    unique_id = str(uuid.uuid4())
    redis_client.publish("go-crawler-commands", url+","+unique_id)
    return JsonResponse({"resultsURL": "https://"+request.META['HTTP_HOST']+"/crawl/"+unique_id})


@require_http_methods(["GET"])
def lookup_crawl(request, crawl_ID=None):
    results_list_key = "go-crawler-results-" + crawl_ID
    print(results_list_key)

    raw_results = redis_client.lrange(
        results_list_key, 0, redis_client.llen(results_list_key))
    #     structured_data = json.loads(str(message.get('data')))

    results = [json.loads(v) for v in raw_results]
    return JsonResponse({"result": results})
