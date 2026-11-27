import biblib.bib
import biblib.messages
import biblib.algo
import sys
import yaml
import os.path
from os import path
import glob

MONTHS = 'January February March April May June July August September October November December'.split()

def clean_entry(ent):

    to_return = {}
    to_return.update(ent)

    if 'title' in ent:
        to_return["title"] = ('  ' + biblib.algo.tex_to_unicode(biblib.algo.title_case(
            ent['title'], pos=ent.field_pos['title'])))

    if 'author' in ent:
        authors = [
            biblib.algo.tex_to_unicode(author.pretty(),
                                       pos=ent.field_pos['author'])
            for author in ent.authors()]
        if len(authors) == 0:
            author = None
        elif len(authors) == 1:
            author = authors[0]
        else:
            author = ', '.join(authors[:-1])
            if len(authors) > 2:
                author += ','
            if ent.authors()[-1].is_others():
                author += ' et al.'
            else:
                author += ' and ' + authors[-1]
        if author:
            to_return["author"] = author

    if 'year' in ent:
        year = ('  {}'.format(ent['year']))
        to_return["year"] = year
    to_return["key"] = ent.key

    #Check if there's an associated pdf:
    pdf_path = os.path.join("resources","pubpdfs","{}.pdf".format(ent.key))
    if path.exists(pdf_path):
        to_return["pdf_path"] = pdf_path
    
    #Check for a thumbnail:
    thumb_path = os.path.join("resources","thumbnails","{}.*".format(ent.key))
    print(thumb_path)
    matches = glob.glob(thumb_path)
    if matches:
        to_return["thumb_path"] = matches[0]
    return to_return


with open('me.bib') as bibtex_file:
    my_bib = bibtex_file.read()
    db = biblib.bib.Parser().parse(my_bib, log_fp=sys.stderr).get_entries()
    for ent in db.values():

        cleaned = clean_entry(ent)

        if ent.typ == "poster":
            collection = "_posters"
        else:
            collection = "_publications"
        out_dest = "{collection}/{ent.key}.md".format(collection=collection, ent=ent)
        
        if not path.exists(out_dest):
            out_file = open(out_dest, "w")
            out_file.write("---\n")
            yaml.dump(cleaned, out_file, allow_unicode=True)
            out_file.write("---")
            out_file.close()       
