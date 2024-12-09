import argparse
import os

from github import Auth, Github

class Style:
    ERROR = '\033[31m'
    WARNING = '\033[33m'
    ENDS = '\033[0m'

pas = os.getenv('GH_PAS')

def arguments():
    parser = argparse.ArgumentParser(description='Github Automator')
    parser.add_argument('-r', '--repos', required=True,
                        help='List of repositories to look for, separated by semicolon', )
    parser.add_argument('-dc', '--delete_comments',
                        help='List of substrings based on which to delete comments, separated by semicolon')
    args = parser.parse_args()
    return {'repos': args.repos, 'delete_comments': args.delete_comments}

def repositories(user, args):
    search_repos = args['repos'].split(';')
    repos = []
    for repo in user.get_repos():
        if repo.name in search_repos:
            repos.append(repo)
    return repos

def search(comments, search_comments, found_comments):
    for sc in search_comments:
        for comment in comments:
            fc = sc.split(':')[0]
            if fc in comment.body:
                if not fc in found_comments:
                    found_comments[fc] = []
                found_comments[fc].append(comment)
    return found_comments

def delete_comments_int(found_comments, search_comments):
    for fc in found_comments:
        fc_offset = None
        for sc in search_comments:
            if fc in sc:
                cnt = sc.split(':')[1]
                try:
                    cnt = int(cnt)
                except ValueError:
                    cnt = 1
                fc_offset = cnt
        fc_desc = sorted(found_comments[fc], key=lambda x: x.updated_at, reverse=True)
        for comment in fc_desc[fc_offset:]:
            comment.delete()
            print(f'Comment {comment.id} deleted')

def delete_comments(pull, args):
    search_comments = args['delete_comments'].split(';')
    found_comments = {}
    comments = pull.get_review_comments()
    found_comments = search(comments, search_comments, found_comments)
    comments = pull.get_issue_comments()
    found_comments = search(comments, search_comments, found_comments)
    delete_comments_int(found_comments, search_comments)

def process(user, repos, args):
    for repo in repos:
        pulls = repo.get_pulls(state='open', sort='updated', direction='desc')
        for pull in pulls:
            if pull.user.login == user.login:
                print(f'Processing PR {pull.title}')
                delete_comments(pull, args)


def main():
    if not pas:
        print(f'{Style.ERROR}GH_PAS environment variable not set{Style.ENDS}')
        return

    args = arguments()
    api = Github(auth=Auth.Token(pas))
    user = api.get_user()

    repos = repositories(user, args)

    process(user, repos, args)

    api.close()

if __name__ == '__main__':
    main()
