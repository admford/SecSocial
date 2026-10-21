SecSocial: meetup list page + search engine files

Upload everything to the repo root (the .github folder is hidden on a Mac:
press Cmd+Shift+. in Finder). Upload all of it in one commit.

  meetups.html                          <- NEW: the list page, generated from your current meetups.json
  index.html                            <- UPDATED: "Browse all meetups as a list" link + search/preview tags
  robots.txt                            <- NEW
  sitemap.xml                           <- NEW: lists the map and the list page
  .github/scripts/build_list.py         <- NEW: turns meetups.json into meetups.html
  .github/workflows/build-list.yml      <- NEW: rebuilds the list when you edit meetups.json by hand
  .github/workflows/add-meetup.yml      <- UPDATED: rebuilds the list on approval
  .github/workflows/remove-meetup.yml   <- UPDATED: rebuilds the list on removal

meetups.json isn't included and doesn't change.
Don't edit meetups.html by hand: it's rebuilt from meetups.json and your edits would be overwritten.
