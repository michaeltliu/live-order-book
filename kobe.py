import requests
from bs4 import BeautifulSoup

link = 'https://www.statmuse.com/nba/ask?q=nba+%s-%s+true+shooting+percentage+leaders'
d = dict()

for i in range(20):
    r = requests.get(link % (1996+i, 1997+i))
    soup = BeautifulSoup(r.text, 'html.parser')
    a = soup.find_all('td',{'class':'text-left px-2 py-2.5 sticky left-0 bg-gray-8 dark:bg-gray-3'})
    n = 0
    for td in a:
        if n >= 25:
            break
        player = td.find('a')['title']
        if player == 'Kobe Bryant':
            print(1996+i, 1997+i)
        d[player] = d.get(player, 0) + 1
        n += 1

print({k: v for k, v in sorted(d.items(), key=lambda item: item[1])})