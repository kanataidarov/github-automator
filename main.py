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
            if sc in comment.body:
                if not sc in found_comments:
                    found_comments[sc] = []
                found_comments[sc].append(comment)
    return found_comments

def delete_comments_int(found_comments):
    for sc in found_comments:
        last_comment = None
        for comment in found_comments[sc]:
            if not last_comment or last_comment.updated_at < comment.updated_at:
                last_comment = comment
        for comment in found_comments[sc]:
            if comment.id != last_comment.id:
                comment.delete()
                print(f'Comment {comment.id} deleted')

def delete_comments(user, repos, args):
    search_comments = args['delete_comments'].split(';')
    for repo in repos:
        pulls = repo.get_pulls(state='open', sort='updated', direction='desc')
        for pull in pulls:
            if pull.user.login == user.login:
                print(f'Processing PR {pull.title}')
                found_comments = {}
                comments = pull.get_review_comments()
                found_comments = search(comments, search_comments, found_comments)
                comments = pull.get_issue_comments()
                found_comments = search(comments, search_comments, found_comments)
                delete_comments_int(found_comments)

def main():
    if not pas:
        print(f'{Style.ERROR}GH_PAS environment variable not set{Style.ENDS}')
        return

    args = arguments()
    api = Github(auth=Auth.Token(pas))
    user = api.get_user()

    repos = repositories(user, args)

    delete_comments(user, repos, args)

    api.close()

if __name__ == '__main__':
    main()
