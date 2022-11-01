import pyperclip
import requests
from bs4 import BeautifulSoup
from typing import TypedDict

Answer = TypedDict('答え情報', {'answer': str, 'text': str, 'link': str, 'recommend': bool})


def main():
    print('### 試験スクレイパー v1')
    print('[+] クリップボードにワードが書き込まれると、自動的に検索します。\n')
    while True:
        try:
            #word = input('[Word]: ') # 入力モードにしたい場合はここをコメントアウト
            word = pyperclip.waitForNewPaste()
            print('[?] ' + word + '\n')

            ans_info = get_answer_withword(word)
            rank = 1
            for ans in ans_info:
                print('    [' + str(rank) + '] ' + ('(推奨) ' if ans['recommend'] else '') + ans['link'])
                print('    [' + str(rank) + '] ' + ans['answer'] + ': ' + ans['text'] + '\n')
                rank += 1
        except Exception as e:
            print('    [-] ' + str(e))
        except KeyboardInterrupt:
            break
        print('')


def get_googlesearch_rank_withlink(search_word: str, page: int = 10) -> list[str]:
    url = f'https://www.google.co.jp/search?hl=ja&num={page}&q={search_word}'
    request = requests.get(url)

    soup = BeautifulSoup(request.text, "html.parser")
    search_site_list = soup.select('div.kCrYT > a')

    ranks_link = []
    for rank, site in zip(range(1, page + 1), search_site_list):
        site_url = site['href'].replace('/url?q=', '')
        ranks_link.append(site_url)

    return ranks_link


def parse_siken_webpage(request_text: str, word: str, link: str) -> Answer:
    ANS_SELECT = {'ア': 'a', 'イ': 'i', 'ウ': 'u', 'エ': 'e', 'オ': 'o'}
    ANS_SELECT_NUM = {'ア': 0, 'イ': 1, 'ウ': 2, 'エ': 3, 'オ': 4}
    word = word.replace('、', '，')

    try:
        soup = BeautifulSoup(request_text, "html.parser")
        ans_el = soup.select('#answerChar')
        ans = ''
        ansText = ''

        if len(ans_el) > 0:
            ans = ans_el[0].text
            ansText = soup.select('#select_' + ANS_SELECT[ans])[0].text
        else:
            ans = soup.select('#true')[0].text
            ansText = soup.select('.selectList')[
                0].contents[ANS_SELECT_NUM[ans]].text

        return {'answer': ans, 'text': ansText, 'link': link, 'recommend': word in soup.select('main')[0].text}
    except:
        return None


def get_answer_withword(word: str) -> list[Answer]:
    ranks_link = get_googlesearch_rank_withlink(word)
    if len(ranks_link) <= 0:
        raise Exception('Google検索にヒットしませんでした。')

    ans_links = []
    for link in ranks_link:
        if '-siken.com' in link:
            ans_links.append(link.split('&sa=')[0])

    if len(ans_links) <= 0:
        raise Exception('ランキング内に試験情報が見つかりません。')

    ans_info = []
    for ans_link in ans_links:
        request = requests.get(ans_link)
        ans = parse_siken_webpage(request.text, word, ans_link)
        if ans is None:
            continue
        ans_info.append(ans)

    if len(ans_info) <= 0:
        raise Exception('試験情報内で答えが見つかりません。')

    ans_info_recommends = []
    for ans in ans_info:
        if ans['recommend']:
            ans_info_recommends.append(ans)
            break

    if len(ans_info_recommends) <= 0:
        ans_info_recommends = ans_info

    return ans_info_recommends


if __name__ == "__main__":
    main()
