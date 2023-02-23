import pandas

def getpokemons(pokemon=None):
    if pokemon:
        csvbestand = pandas.read_csv('Pokemon.csv')

        pokemoninfo = 'Not found'

        for i, pok in csvbestand.iterrows():
            if pok['Name'] == pokemon:
                pokemoninfo = str(pok)
        return pokemoninfo
    else:
        return 'No search'
    #print(str(len(legendaries))+' Legendary pokemons: ')
    #for x in legendaries:
    #    print(x)

    #print('Average attack: '+ str(sum(attacks) / len(attacks)))