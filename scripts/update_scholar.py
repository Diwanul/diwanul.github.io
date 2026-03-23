import json
import os
from scholarly import scholarly

def fetch_publications(scholar_id):
    print(f"Fetching publications for {scholar_id}...")
    try:
        author = scholarly.search_author_id(scholar_id)
        # Fetching basic info and publications
        author = scholarly.fill(author, sections=['publications'])
        
        publications = []
        for pub in author['publications']:
            pub_filled = scholarly.fill(pub)
            bib = pub_filled.get('bib', {})
            
            title = bib.get('title', '')
            authors = bib.get('author', '')
            venue = bib.get('venue', bib.get('journal', ''))
            year = bib.get('pub_year', '')
            url = pub_filled.get('pub_url', '')

            # Format venue & year
            venue_year = f"{venue}, {year}" if venue and year else venue or year
            
            # Use publication title nicely slugified as an expected image path reference
            slug_title = "".join(x for x in title if x.isalnum() or x.isspace()).replace(" ", "_").lower()
            
            # Check if there is an existing json to merge manually added keys (like pdf, code, image links)
            publications.append({
                "title": title,
                "authors": authors.replace(' and ', ', '),
                "venue": venue_year,
                "venue_clean": venue,
                "year": year, # store year for sorting
                "url": url,
                "project": "",
                "code": "",
                "image": f"images/{slug_title}.png",
                "pdf": ""
            })
            
            # Limit to recent/top 15 to avoid long execution times
            if len(publications) >= 15:
                break
                
        # Sort publications by year descending
        publications.sort(key=lambda x: str(x.get('year', '0')), reverse=True)

        return publications
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

if __name__ == "__main__":
    SCHOLAR_ID = '_vJT64QAAAAJ'
    pubs = fetch_publications(SCHOLAR_ID)
    
    if pubs:
        os.makedirs('data', exist_ok=True)
        # Attempt to retain custom user manual fields from the old json file
        existing_pubs_map = {}
        if os.path.exists('data/publications.json'):
            with open('data/publications.json', 'r') as f:
                old_data = json.load(f)
                for item in old_data:
                    existing_pubs_map[item['title']] = item

        # Save publications
        with open('data/publications.json', 'w') as f:
            # Merge logic for old annotations (manual image path, links) with new data
            out_pubs = []
            for p in pubs:
                merged = {k: v for k, v in p.items() if k != 'venue_clean'}
                if merged['title'] in existing_pubs_map:
                    old_p = existing_pubs_map[merged['title']]
                    merged['image'] = old_p.get('image', merged['image'])
                    merged['url'] = old_p.get('url', merged['url'])
                    merged['project'] = old_p.get('project', merged.get('project', ''))
                    merged['code'] = old_p.get('code', merged.get('code', ''))
                    merged['pdf'] = old_p.get('pdf', merged.get('pdf', ''))
                out_pubs.append(merged)
                
            json.dump(out_pubs, f, indent=2)
            
        # Generate News from the most recent 5 publications based on venue context
        news = []
        for pub in pubs[:5]:
            year = pub.get('year', '')
            year_str = f"[{year}] " if year else ""
            venue = str(pub.get('venue_clean', '')).lower()
            title = pub.get('title', '')
            
            if 'arxiv' in venue:
                content = f"{year_str}🎉 Our paper <strong>\"{title}\"</strong> is available on arXiv!"
            elif venue:
                # Assuming standard conference / journal format string
                content = f"{year_str}🔥 Our paper <strong>\"{title}\"</strong> has been accepted to <em>{pub.get('venue_clean')}</em>!"
            else:
                content = f"{year_str}🚀 New paper <strong>\"{title}\"</strong> is available online!"
                
            news.append({
                "date": year,
                "content": content
            })
            
        with open('data/news.json', 'w') as f:
            json.dump(news, f, indent=2)
            
        print("Publications and News updated successfully.")
    else:
        print("No publications fetched or an error occurred.")
