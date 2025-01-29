from playwright.sync_api import sync_playwright
import pandas as pd
import pickle  # for saving and loading cookies
import time

# Load cookies from the saved file
def load_cookies(context, cookies_file):
    with open(cookies_file, "rb") as f:
        cookies = pickle.load(f)
        context.add_cookies(cookies)

def scrape_player_data():
    with sync_playwright() as p:
        # Launch the browser in visible mode for debugging
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
        )

        # Load cookies to maintain the logged-in session
        cookies_file = "cookies.pkl"  # Specify the path to your cookies file
        load_cookies(context, cookies_file)

        page = context.new_page()

        # URL to scrape
        url = "https://basketball.fantasysports.yahoo.com/nba/969/players"
        try:
            print(f"Navigating to {url}...")
            page.goto(url, timeout=60000, wait_until="domcontentloaded")

            # Locate the stats dropdown and get all options
            stats_dropdown = page.locator("#statselect")
            options = stats_dropdown.locator("option")
            option_count = options.count()
            print(f"Found {option_count} stat options.")

            # Dictionary to store data for each stat option
            all_data = {}

            for i in range(1,2):
                # Select the current stat option
                option_value = options.nth(i).get_attribute("value")
                option_text = options.nth(i).inner_text().strip()
                print(f"Selecting stat option: {option_text} ({option_value})")
                stats_dropdown.select_option(option_value)

                # Wait for the players table to reload
                page.wait_for_timeout(2000)  # Adjust timeout if necessary

                # Extract all pages of data for the current stat option
                player_data = []

                while True:
                    # Extract player data from the current page
                    print("Extracting player data from current page...")
                    players_table = page.locator("div.players tbody")
                    player_rows = players_table.locator("tr")
                    total_rows = player_rows.count()

                    for j in range(total_rows):
                        row = player_rows.nth(j)
                        player = row.locator("a.Nowrap.name.F-link.playernote")
                        status = row.locator("td.Alt.Ta-start.Nowrap.Bdrend")
                        team = row.locator("span.D-b")
                        points = row.locator("span.Fw-b")
                        per_ros_value = row.locator("td").nth(9)
                        mpg = row.locator("td").nth(10)
                        pts = row.locator("td").nth(11)
                        reb = row.locator("td").nth(12)
                        ast = row.locator("td").nth(13)
                        st = row.locator("td").nth(14)
                        blk = row.locator("td").nth(15)
                        to = row.locator("td").nth(16)
                        
                        # Locate and click the radio button
                        radio = row.locator('a.Nowrap.name.F-link.playernote')
                        radio.scroll_into_view_if_needed()
                        # radio.wait_for_element_state('a.Nowrap.name.Flink.playernote',state = 'visible')  # Ensure the element is visible
                        radio.click()

                        # Wait for the player card to load and extract news
                        page.wait_for_selector('#player-note-content', timeout=50000)  # Wait for the player card to appear
                        player_card = page.locator('#player-note-content')
                        def wait_for_full_player_notes():
                            max_attempts = 10  # Max number of attempts to check for full content
                            for attempt in range(max_attempts):
                                player_notes = player_card.locator("css=section.player-notes").text_content(timeout=5000)
                                if "Complete content indicator text" in player_notes:  # Replace with a unique indicator in the notes
                                    return player_notes

                                time.sleep(1)

                            return player_notes
                        player_news = wait_for_full_player_notes()
                        print(player_news)


                        # Close the player note content
                        page.locator('svg[data-icon="close"]').click()
                        
                                            
                        player_data.append({
                            "name": player.get_attribute("title") if player.count() > 0 else "N/A",
                            "link": player.get_attribute("href") if player.count() > 0 else "N/A",
                            "roster_status": status.inner_text().strip() if status.count() > 0 else "N/A",
                            "nba_team": team.inner_text().strip() if team.count() > 0 else "N/A",
                            "fan_points": points.inner_text().strip() if points.count() > 0 else "N/A",
                            "per_ros_value": per_ros_value.inner_text().strip() if per_ros_value.count() > 0 else "N/A",
                            "mpg": mpg.inner_text().strip() if mpg.count() > 0 else "N/A",
                            "pts": pts.inner_text().strip() if pts.count() > 0 else "N/A",
                            "reb": reb.inner_text().strip() if reb.count() > 0 else "N/A",
                            "ast": ast.inner_text().strip() if ast.count() > 0 else "N/A",
                            "st": st.inner_text().strip() if st.count() > 0 else "N/A",
                            "blk": blk.inner_text().strip() if blk.count() > 0 else "N/A",
                            "to": to.inner_text().strip() if to.count() > 0 else "N/A",
                            "player_notes": player_news if player_news else "N/A",  

                            
                        })

                    # Check if the "Next 25" button exists and is clickable
                    try:
                        next_button = page.locator("li.last.Inlineblock a:has-text('Next 25')")
                        if next_button.is_visible():
                            print("Clicking 'Next 25' button...")
                            next_button.click()
                            time.sleep(2)  # Short delay for content to load
                        else:
                            print("No more players to load.")
                            break
                    except Exception as e:
                        print("Error while clicking 'Next 25':", e)
                        break


                # Save data for the current stat option
                all_data[option_text] = pd.DataFrame(player_data)

            # Save all data to an Excel file with multiple sheets
            output_file = "player_data_969.xlsx"
            with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
                for stat_name, df in all_data.items():
                    df.to_excel(writer, sheet_name=stat_name[:31], index=False)  # Excel sheet names max 31 chars

            print(f"Data saved to {output_file}")

        except Exception as e:
            print(f"Error while scraping: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    scrape_player_data()
