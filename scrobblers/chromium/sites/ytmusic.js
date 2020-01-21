maloja_scrobbler_selector_playbar = "//ytmusic-player-bar"


maloja_scrobbler_selector_metadata = ".//div[contains(@class,'middle-controls')]/div[contains(@class,'content-info-wrapper')]"

maloja_scrobbler_selector_title = ".//yt-formatted-string[contains(@class,'title')]/@title"
maloja_scrobbler_selector_artists = ".//span/span[contains(@class,'subtitle')]/yt-formatted-string/a[position()<last()]"
maloja_scrobbler_selector_artist = "./text()"
maloja_scrobbler_selector_duration = ".//div[contains(@class,'left-controls')]/span[contains(@class,'time-info')]/text()"
duration_needs_split = true


maloja_scrobbler_selector_control = ".//div[contains(@class,'left-controls')]/div/paper-icon-button[contains(@class,'play-pause-button')]/@title"
