import httplib2
from bs4 import BeautifulSoup, SoupStrainer
import re
import numpy as np


def without_slash_at_end_and_without_query_string(url):
    components = url.split('?')
    if len(components) > 1:
        url = components[0]
    if url[-1] == '/':
        return url[:-1]
    return url


def format_uri(uri, base_url):
    if re.match('http(s)?://.*', uri):
        return without_slash_at_end_and_without_query_string(uri)
    if re.match('/.*', uri):
        return without_slash_at_end_and_without_query_string(base_url + uri)
    return None


def crawl_links(page, domain=None, links=set()):
    print(page)
    if not domain:
        domain = page
    http = httplib2.Http()
    status, response = http.request(page)
    for link in BeautifulSoup(response, parse_only=SoupStrainer('a'), features="html.parser"):
        if link.has_attr('href'):
            formatted_link = format_uri(link['href'], domain)
            if formatted_link and formatted_link not in links and formatted_link.startswith(domain):
                links.add(formatted_link)
                sub_page_links = crawl_links(formatted_link, domain, links)
                links = links.union(sub_page_links)
    return list(links)


def outgoing_links(page, domain=None):
    if not domain:
        domain = page
    http = httplib2.Http()
    status, response = http.request(page)
    links = {}
    for link in BeautifulSoup(response, parse_only=SoupStrainer('a'), features="html.parser"):
        if link.has_attr('href'):
            formatted_link = format_uri(link['href'], domain)
            if formatted_link and formatted_link.startswith(domain):
                if formatted_link in links:
                    links[formatted_link] += 1
                else:
                    links[formatted_link] = 1
    return links


def normalizer_of(outgoing_links_to_count):
    normalizer = 0
    for outgoing_link, count in outgoing_links_to_count.items():
        normalizer += count
    return normalizer


def web_matrix(links, domain):
    n = len(links)
    mat = np.zeros((n, n))
    for i in range(n):
        outgoing_links_to_count = outgoing_links(links[i], domain)
        normalizer = normalizer_of(outgoing_links_to_count)
        for j in range(n):
            if links[j] in outgoing_links_to_count:
                mat[j][i] = outgoing_links_to_count[links[j]] / normalizer
    return mat


def power_iteration(mat):
    assert mat.shape[0] == mat.shape[1]
    n = mat.shape[0]
    v = np.array(list(map(lambda _: 1 / n, range(n))))
    for i in range(1000):
        product = mat.dot(v)
        v = product / np.linalg.norm(product)
    return v


def page_rank(pages, eigen_vector):
    page_rank_lst = []
    for i in range(len(pages)):
        page_rank_lst.append((pages[i], eigen_vector[i]))
    return list(reversed(sorted(page_rank_lst, key=lambda item: item[1])))


domain = 'http://goerlitz.de'

print(outgoing_links(domain))

pages = crawl_links(domain)
print(pages)
print()
print(len(pages))

matrix = web_matrix(pages, domain)
print(matrix)

page_rank = page_rank(pages, power_iteration(matrix))
print(page_rank)
