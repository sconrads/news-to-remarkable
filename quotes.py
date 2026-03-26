# quotes.py - Daglige visdomsord. Plukker ett sitat per dag basert på dato.

import hashlib
from datetime import date

QUOTES = [
    ("Den som ikke risikerer noe, risikerer alt.", "Jean-Paul Sartre"),
    ("Livet måles ikke i antall åndedrag, men i øyeblikk som tar pusten fra deg.", "Maya Angelou"),
    ("Det er ikke hvem du er som holder deg tilbake — det er hvem du tror du ikke er.", "Denis Waitley"),
    ("Fremtiden tilhører dem som tror på sine drømmers skjønnhet.", "Eleanor Roosevelt"),
    ("Suksess er ikke endelig, fiasko er ikke fatal — det er motet til å fortsette som teller.", "Winston Churchill"),
    ("Det er i mørket du finner stjernene.", "Aristoteles"),
    ("Den beste måten å forutsi fremtiden på er å skape den.", "Peter Drucker"),
    ("Kunnskap er makt.", "Francis Bacon"),
    ("Det eneste jeg vet er at jeg ikke vet noe.", "Sokrates"),
    ("Vær den forandringen du ønsker å se i verden.", "Mahatma Gandhi"),
    ("Lev som om du skal dø i morgen. Lær som om du skal leve for alltid.", "Mahatma Gandhi"),
    ("I midten av vanskeligheter ligger muligheter.", "Albert Einstein"),
    ("Det er ikke tankene som definerer deg, men handlingene.", "Albert Einstein"),
    ("Et menneske som aldri har gjort feil, har aldri prøvd noe nytt.", "Albert Einstein"),
    ("Tid er penger.", "Benjamin Franklin"),
    ("Fortell meg og jeg glemmer. Lær meg og jeg husker. Involver meg og jeg lærer.", "Benjamin Franklin"),
    ("Den eneste måten å gjøre godt arbeid på er å elske det du gjør.", "Steve Jobs"),
    ("Kreativitet er å koble sammen ting.", "Steve Jobs"),
    ("Din tid er begrenset — ikke kast den bort på å leve andres liv.", "Steve Jobs"),
    ("Det som ikke dreper deg, gjør deg sterkere.", "Friedrich Nietzsche"),
    ("Uten musikk ville livet vært en feil.", "Friedrich Nietzsche"),
    ("Lykke er ikke et mål i seg selv — det er et biprodukt av et liv godt levd.", "Eleanor Roosevelt"),
    ("Gjør alltid det du er redd for.", "Ralph Waldo Emerson"),
    ("Det er lettere å bygge sterke barn enn å reparere ødelagte voksne.", "Frederick Douglass"),
    ("Ikke gå hvor stien leder — gå der det ikke er noen sti og legg igjen et spor.", "Ralph Waldo Emerson"),
    ("Ekte vennskap er langsomt voksende planter.", "George Washington"),
    ("Vi er det vi gjentatte ganger gjør. Dyktighet er derfor ikke en handling, men en vane.", "Aristoteles"),
    ("Det å kjenne seg selv er begynnelsen på all visdom.", "Aristoteles"),
    ("Lykken er aktivitetens fylde.", "Aristoteles"),
    ("Hvert eventyr krever et første skritt.", "Lewis Carroll"),
    ("Drøm stort. Start smått. Handle nå.", "Robin Sharma"),
    ("Det er ikke lengden på livet som teller, men dybden.", "Ralph Waldo Emerson"),
    ("Jo mer du leser, desto mer vil du vite. Jo mer du lærer, desto mer steder vil du gå.", "Dr. Seuss"),
    ("Eneste grensen for vår realisering av i morgen er tvilen vi har i dag.", "Franklin D. Roosevelt"),
    ("Ting fungerer ut fra nødvendighet det som er mulig skjer bare gjennom initiativ.", "Ingvar Kamprad"),
    ("Det er ikke størrelsen på hunden i kampen — det er størrelsen på kampen i hunden.", "Mark Twain"),
    ("Sannhet er sjelden ren og aldri enkel.", "Oscar Wilde"),
    ("Vi har alle to liv. Det andre begynner når vi innser at vi bare har ett.", "Confucius"),
    ("Veien til suksess og veien til fiasko er nesten nøyaktig den samme.", "Colin R. Davis"),
    ("Ditt liv blir ikke bedre av en tilfeldighet — det blir bedre ved forandring.", "Jim Rohn"),
    ("Klatring på stigen til suksess er lettere om du holder hendene rene.", "Brian Tracy"),
    ("Det du fokuserer på vokser.", "Robin Sharma"),
    ("Smil er det korteste avstanden mellom to mennesker.", "Victor Borge"),
    ("Gjør det du kan, med det du har, der du er.", "Theodore Roosevelt"),
    ("Takknemlighet er ikke bare den største av dyder, men moren til alle andre.", "Cicero"),
    ("Livet er ti prosent det som skjer med deg og nitti prosent hvordan du reagerer på det.", "Charles R. Swindoll"),
    ("En reise på tusen mil begynner med ett skritt.", "Lao Tzu"),
    ("Naturens dypeste hemmelighet er måten kraften spiller gjennom oss.", "Ralph Waldo Emerson"),
    ("Kjærlighet er den eneste kraften som kan gjøre et fiende til en venn.", "Martin Luther King Jr."),
    ("Hold hodet høyt, og ikke la noen tvile på din verdi.", "Oprah Winfrey"),
    ("Det finnes ingen heiser til suksess. Du må ta trappene.", "Zig Ziglar"),
]


def get_quote_of_the_day(today: date = None) -> tuple:
    """
    Returnerer (sitat, forfatter) for dagens dato.
    Bruker datoen som deterministisk seed — samme sitat hele dagen.
    """
    if today is None:
        today = date.today()
    day_str = today.isoformat()
    digest = int(hashlib.md5(day_str.encode()).hexdigest(), 16)
    idx = digest % len(QUOTES)
    return QUOTES[idx]
