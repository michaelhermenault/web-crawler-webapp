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
    redis_client.publish("go-crawler-commands", "{},{}".format(url, unique_id))
    return JsonResponse({"resultsURL": build_results_link(request.META['HTTP_HOST'], unique_id, 0)}, status=202)


@ require_http_methods(["GET"])
def lookup_crawl(request, crawl_ID=None):
    start_string = request.GET.get("startIndex")
    if start_string is None:
        return JsonResponse({"message": "Must specify starting index"}, status=400)
    try:
        start_index = int(start_string)
    except ValueError:
        return JsonResponse({"message": "Invalid data type in query params"}, status=400)

    results_list_key = "go-crawler-results-{}".format(crawl_ID)

    raw_results = redis_client.lrange(
        results_list_key, start_index, redis_client.llen(results_list_key))

    # No new results found
    if len(raw_results) == 0:
        return JsonResponse({"_links": {"next": {"href": build_results_link(request.META['HTTP_HOST'], crawl_ID, start_index)}}, "edges": []})

    results = [json.loads(v) for v in raw_results]

    if results[-1].get('DoneMessage') is not None:
        return JsonResponse({"edges": results})
    return JsonResponse({"_links": {"next": {"href": build_results_link(request.META['HTTP_HOST'], crawl_ID, start_index+len(results))}}, "edges": results})


def build_results_link(host, unique_id, start_index):
    return "http://{}/crawl/{}?startIndex={}".format(host, unique_id, start_index)
