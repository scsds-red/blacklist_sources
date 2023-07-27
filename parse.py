from urllib import request
import requests
from git import Repo
import json
import tarfile, os

hosts_err = []
blacklist_uniq = set()
PATH_OF_GIT_REPO = "/opt/membrana_blacklist"
blacklist_dict = {}


# get dict of sources from json
def read_urls_json():
    path_sources_json = f"{PATH_OF_GIT_REPO}/urls.json"
    with open(path_sources_json) as sources_json:
        sources_dict = json.load(sources_json)
    return sources_dict


# parse urls from json and return strings
def parse_urls(source):
    resp = requests.get(url=source["url"], headers={"User-Agent": "Mozilla/5.0"})
    hostlines = resp.text.split("\n")
    hostlines = [
        line.strip()
        for line in hostlines
        if not line.startswith("!") and line.strip() != ""
    ]
    return hostlines


# processing of strings from sources
def process_lines(source):
    hostlines = parse_urls(source)
    for line in hostlines:
        try:
            split_line = line.split()
            if source["format"] == "easy" and line not in blacklist_uniq:
                blacklist_uniq.add(line)
                blacklist_dict.setdefault(str(source["type"]), []).append(str(line))
            elif (
                source["format"] == "host"
                and not line.startswith("#")
                and split_line[0] not in blacklist_uniq
            ):
                blacklist_uniq.add(split_line[0])
                blacklist_dict.setdefault(str(source["type"]), []).append(
                    str("||" + split_line[0] + "^")
                )
            elif (
                source["format"] == "ip_host"
                and not line.startswith("#")
                and split_line[1] not in blacklist_uniq
            ):
                blacklist_uniq.add(split_line[1])
                blacklist_dict.setdefault(str(source["type"]), []).append(
                    str("||" + split_line[1] + "^")
                )
        except:
            continue


# function for generating a blacklist
def create_lists():
    sources_dict = read_urls_json()
    sources = sources_dict["urls"]
    for source in sources:
        try:
            process_lines(source)
        except request.URLError as err:
            hosts_err.append(source["url"])
            continue
        print(source["url"], "--", len(blacklist_dict), "\n", hosts_err)
    return blacklist_dict


# write blacklist to files in local catalog
def write_json():
    with open(f"{PATH_OF_GIT_REPO}/blacklist.json", "w") as t:
        json.dump(blacklist_dict, t, ensure_ascii=False, indent=4)
    with tarfile.open(f"{PATH_OF_GIT_REPO}/blacklist.tar.gz", "w:gz") as tar:
        tar.add(
            f"{PATH_OF_GIT_REPO}/blacklist.json",
            arcname=os.path.basename(f"{PATH_OF_GIT_REPO}/blacklist.json"),
        )
    os.remove(f"{PATH_OF_GIT_REPO}/blacklist.json")


# push to github repo
def git_push(repo, origin):
    COMMIT_MESSAGE = "update blocklists"
    try:
        repo.git.add(all=True)
        repo.index.commit(COMMIT_MESSAGE)
        origin.push()
        print("success push")
    except:
        print("Some error occured while pushing the code")


# pull from github repo
def git_pull(origin):
    try:
        origin.pull()
        print("success pull")
    except:
        print("Some error occured while pulling the code")


def main():
    repo = Repo(PATH_OF_GIT_REPO)
    origin = repo.remotes.origin
    git_pull(origin)
    create_lists()
    write_json()
    git_push(repo, origin)


main()
