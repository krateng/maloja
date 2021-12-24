maloja_scrobbler_selector_playbar = "//div[contains(@class,'trackView')]"


maloja_scrobbler_selector_metadata = "."
// need to select everything as bar / metadata block because artist isn't shown in the inline player

maloja_scrobbler_selector_title = ".//span[@class='title']/text()"
maloja_scrobbler_selector_artist = ".//span[contains(@itemprop,'byArtist')]/a/text()"
maloja_scrobbler_selector_duration = ".//span[@class='time_total']/text()"


maloja_scrobbler_selector_control = ".//td[@class='play_cell']/a[@role='button']/div[contains(@class,'playbutton')]/@class"

maloja_scrobbler_label_playing = "playbutton playing"
maloja_scrobbler_label_paused = "playbutton"
