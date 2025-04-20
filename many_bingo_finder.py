from bs4 import BeautifulSoup
import requests
import pandas as pd
import pickle
import re
import copy


def find_no_score_move(s: str, no_score_reason: str):
    showmove_matches = list(re.finditer(r"showmove\((\d+)\)", s))

    # Step 2: Find all "Lost challenge" positions
    lost_matches = list(re.finditer(no_score_reason, s))

    # Step 3: For each Lost challenge, find the last showmove before it
    results = []

    for lost in lost_matches:
        lost_index = lost.start()
        # Filter showmoves before this Lost challenge
        candidates = [m for m in showmove_matches if m.start() < lost_index]
        if candidates:
            last_showmove = candidates[-1]
            results.append(last_showmove.group(1))  # just the digits
        else:
            results.append(None)  # or whatever you want for "no match"

    return results


def is_sublist(ls1: list, ls2: list) -> bool:
    for item in ls1:
        if item in ls2:
            ls2.remove(item)
        else:
            return False
    return True


def played_all_seven(rack: str, play: str) -> bool:
    if play in ["EXCHANGE", "LOST CHALLENGE", "Exchange", "Lost Challenge"]:
        return False
    if '-chl-' in play:
        return False
    if is_sublist(list(rack), list(play)) and len(play)>=7:
        return True
    if '?' in rack:
        rack_real = list(rack)
        rack_real.remove('?')
        if is_sublist(rack_real, list(play)) and rack.upper != rack and len(play)>=7:
            return True
    return False


headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
}

annotated_url = 'https://www.cross-tables.com/'

data = []

for x in range(50):

    offset = str(x) + "01"
    if x == 0:
        offset = "1"
    r = requests.get("https://www.cross-tables.com/annolistself.php?offset=" + offset, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    for row in range(1, 101):
        try:
            player1_bingo_count = 0
            player2_bingo_count = 0
            print([x, row, len(data)])
            broken = 0
            num_words = 0
            game = soup.find("tr", {"id": "row" + str(row)})
            url = game.find("a", href=True)
            annotated_request = requests.get(annotated_url + url['href'], headers=headers)
            full_url = annotated_url + url['href']
            annotated_soup = BeautifulSoup(annotated_request.text, "html.parser")

            no_score_turns = []
            lost_challenges = find_no_score_move(str(annotated_soup), "Lost challenge")
            lost_challenges = [str(int(x) - 1) for x in lost_challenges]
            challenges = find_no_score_move(str(annotated_soup), "challenge")
            passes = find_no_score_move(str(annotated_soup), "Pass")
            exchanges = find_no_score_move(str(annotated_soup), "Exchange")
            no_score_turns.extend(challenges)
            no_score_turns.extend(passes)
            no_score_turns.extend(exchanges)
            no_score_turns.extend(lost_challenges)

            dictionary = str(annotated_soup).split('Dictionary: <b>')[1].split('</b')[0]

            player1 = str(annotated_soup).split("</div> -->")[1].split(" vs.")[0]
            player1 = player1.split(' <')[0]
            player2 = str(annotated_soup).split("vs. ")[1].split("<")[0]

            player1 = player1.replace('\n', '').replace('\t', '')
            player2 = player2.replace('\n', '').replace('\t', '')

            var_let_plays = str(annotated_soup).split('var letplays = Array(')[1].split(');')[0]
            #print(var_let_plays)
            plays = var_let_plays.split('Array(')
            player1_modulus = 1
            player2_modulus = 0

            for i in range(1, len(plays)):
                if str(i) in no_score_turns and str(i) not in lost_challenges:
                    player1_modulus = (player1_modulus+1) % 2
                    player2_modulus = (player2_modulus + 1) % 2
                    continue
                elif str(i) in lost_challenges:
                    continue
                if i%2 == player1_modulus:
                    active_player = player1
                else:
                    active_player = player2
                p = plays[i]
                matches = re.findall(r"'(.*?)'", p)

                play = matches[0]
                rack = matches[1]

                if played_all_seven(rack, play) and i%2 == player2_modulus:
                    player2_bingo_count += 1
                    active_player = player2
                elif played_all_seven(rack, play) and i%2 == player1_modulus:
                    player1_bingo_count += 1
                    active_player = player1

                #print("%s plays %s from on turn %s." % (active_player, play, str(i)))
                #print([play, player1_modulus, player2_modulus])
            #print(annotated_soup)

            data.append([player1, player1_bingo_count, player2, player2_bingo_count, full_url, dictionary])

        except:
            continue

        df = pd.DataFrame(columns=["Player1",
                                   "Player1 Bingo Count",
                                   "Player2",
                                   "Player2 Bingo Count",
                                   "Game URL",
                                   "Dictionary"
                                   ], data=data)



        df['most_bingoes'] = df[['Player1 Bingo Count', 'Player2 Bingo Count']].max(axis=1)

        df.sort_values(by='most_bingoes', inplace=True, ascending=False)

        df.drop(columns=['most_bingoes'], inplace=True)
        df.to_clipboard(index=False)
        df.to_csv("bingo_counts.csv", index=False)
