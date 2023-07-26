from bs4 import BeautifulSoup
import requests
import pandas as pd
import pickle

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
}

with open('cleaned_words.pkl', 'rb') as f:
    words = pickle.load(f)


def is_phony(ls: list, valid_words: list = words):
    for w in ls:
        if w not in valid_words and w[:8] != "EXCHANGE" and w != "LOST CHALLENGE":
            return True
    return False


annotated_url = 'https://www.cross-tables.com/'

data = []

for x in range(1, 24):
    offset = str(x) + "01"

    r = requests.get("https://www.cross-tables.com/annolistself.php?offset=" + offset, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    for row in range(1, 101):
        broken = 0
        num_words = 0
        game = soup.find("tr", {"id": "row" + str(row)})
        url = game.find("a", href=True)

        annotated_request = requests.get(annotated_url + url['href'], headers=headers)
        annotated_soup = BeautifulSoup(annotated_request.text, "html.parser")

        player1 = str(annotated_soup).split("</div> -->")[1].split(" <a")[0]
        player2 = str(annotated_soup).split("vs. ")[1].split(" <a")[0]

        for i in range(20, 40):  # Crudely find the number of plays in a game.
            num_words = i
            if not annotated_soup.find("a", {"id": "moveselector" + str(i)}):
                num_words = i-1
                break
        played_words = []
        for i in range(num_words):
            try:
                word = str(annotated_soup).split('showmove(' + str(i+1) + '); scroll(0,0);">')[1].split("</a>")[0].upper()
                played_words.append(word)
            except IndexError:
                broken = 1
                break
        if broken != 0:
            broken = 0
        else:
            datum = [player1[4:], player2, url["href"]] + [played_words[:-1]] + [is_phony(played_words[:-1])]

            data.append(datum)

df = pd.DataFrame(columns=["Player1", "Player2", "Game URL", "Played Words", "Phony Played"], data=data)

df.to_csv("phoney_finds.csv", index=False)
