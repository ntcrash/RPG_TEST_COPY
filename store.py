def draw_store_screen(self):
    """Draw the store screen with scrollable item list"""
    self.screen.fill(MENU_BG)

    # Debug info at top-left
    debug_text = f"State: {self.current_state} | ESC to exit"
    debug_surface = pygame.font.Font(None, 16).render(debug_text, True, WHITE)
    self.screen.blit(debug_surface, (10, 10))

    title = self.ui_renderer.large_font.render("🏪 MAGIC SHOP", True, WHITE)
    title_rect = title.get_rect(center=(self.WIDTH // 2, 40))
    self.screen.blit(title, title_rect)

    if not self.character_manager.character_data:
        no_char_text = self.ui_renderer.font.render("No character loaded!", True, WHITE)
        no_char_rect = no_char_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2))
        self.screen.blit(no_char_text, no_char_rect)
        return

    current_credits = self.character_manager.character_data.get("Credits", 0)
    credits_text = self.ui_renderer.font.render(f"💰 Credits: {current_credits}", True, GOLD)
    self.screen.blit(credits_text, (20, 80))

    # Calculate visible items based on scroll
    max_items = len(self.store.items)
    start_index = self.store_scroll_offset
    end_index = min(start_index + self.items_per_page, max_items)

    # Draw store items (left side)
    y_pos = 120
    item_height = 35  # Reduced height for more compact display

    for i in range(start_index, end_index):
        item = self.store.items[i]

        # Determine if player can afford this item
        can_afford = current_credits >= item.price

        # Set colors based on selection and affordability
        if i == self.store.selected_item:
            if can_afford:
                item_color = MENU_SELECTED
                bg_color = MENU_HIGHLIGHT
            else:
                item_color = RED
                bg_color = (100, 50, 50)  # Dark red background

            # Draw selection background
            selection_rect = pygame.Rect(15, y_pos - 3, 370, item_height - 5)
            pygame.draw.rect(self.screen, bg_color, selection_rect)
            pygame.draw.rect(self.screen, item_color, selection_rect, 2)
        else:
            item_color = WHITE if can_afford else GRAY

        # Item name and price (smaller font)
        item_text = f"{item.name} - {item.price}💰"
        text_surface = self.ui_renderer.small_font.render(item_text, True, item_color)
        self.screen.blit(text_surface, (20, y_pos))

        # Item description (even smaller font)
        desc_surface = pygame.font.Font(None, 16).render(item.description[:45], True, MENU_TEXT)
        self.screen.blit(desc_surface, (20, y_pos + 18))

        y_pos += item_height

    # Scroll indicators
    if self.store_scroll_offset > 0:
        # Up arrow
        up_arrow = self.ui_renderer.small_font.render("↑ More items above", True, LIGHT_BLUE)
        self.screen.blit(up_arrow, (20, 100))

    if end_index < max_items:
        # Down arrow
        down_arrow = self.ui_renderer.small_font.render("↓ More items below", True, LIGHT_BLUE)
        self.screen.blit(down_arrow, (20, y_pos + 10))

    # Show selected item details in a panel (right side)
    if self.store.selected_item < len(self.store.items):
        selected_item = self.store.items[self.store.selected_item]

        # Details panel
        details_rect = pygame.Rect(400, 120, 380, 350)
        pygame.draw.rect(self.screen, UI_BG_COLOR, details_rect)
        pygame.draw.rect(self.screen, UI_BORDER_COLOR, details_rect, 2)

        detail_y = 130

        # Item name (header)
        name_surface = self.ui_renderer.font.render(selected_item.name, True, MENU_SELECTED)
        self.screen.blit(name_surface, (410, detail_y))
        detail_y += 35

        # Item details
        details = [
            f"Type: {selected_item.item_type.replace('_', ' ').title()}",
            f"Price: {selected_item.price} credits",
            f"Description: {selected_item.description}"
        ]

        for detail in details:
            # Handle word wrapping for long descriptions
            if detail.startswith("Description:") and len(detail) > 35:
                lines = [detail[:35] + "...", detail[35:70] + "..." if len(detail) > 70 else detail[35:]]
                for line in lines:
                    if line.strip():
                        detail_surface = self.ui_renderer.small_font.render(line, True, WHITE)
                        self.screen.blit(detail_surface, (410, detail_y))
                        detail_y += 18
            else:
                detail_surface = self.ui_renderer.small_font.render(detail, True, WHITE)
                self.screen.blit(detail_surface, (410, detail_y))
                detail_y += 20

        # Effect value
        if selected_item.effect_value > 0:
            if selected_item.item_type in ["health_potion", "mana_potion"]:
                effect_text = f"Restores: {selected_item.effect_value} points"
            elif selected_item.item_type == "weapon":
                effect_text = f"Weapon Damage: +{selected_item.effect_value}"
            elif selected_item.item_type == "armor":
                effect_text = f"Armor Class: +{selected_item.effect_value}"
            else:
                effect_text = f"Effect Value: {selected_item.effect_value}"

            effect_surface = self.ui_renderer.small_font.render(effect_text, True, LIGHT_BLUE)
            self.screen.blit(effect_surface, (410, detail_y))
            detail_y += 25

        # Stat bonuses if applicable
        if selected_item.stat_bonuses:
            detail_y += 10
            bonus_title = self.ui_renderer.small_font.render("Stat Bonuses:", True, MENU_SELECTED)
            self.screen.blit(bonus_title, (410, detail_y))
            detail_y += 20

            for stat, bonus in selected_item.stat_bonuses.items():
                bonus_text = f"+{bonus} {stat.title()}"
                bonus_surface = self.ui_renderer.small_font.render(bonus_text, True, GREEN)
                self.screen.blit(bonus_surface, (420, detail_y))
                detail_y += 18

        # Purchase status
        detail_y += 20
        if current_credits >= selected_item.price:
            status_text = "✅ Can afford this item"
            status_color = GREEN
        else:
            needed = selected_item.price - current_credits
            status_text = f"❌ Need {needed} more credits"
            status_color = RED

        status_surface = self.ui_renderer.small_font.render(status_text, True, status_color)
        self.screen.blit(status_surface, (410, detail_y))

    # Instructions (bottom) - Enhanced to emphasize ESC
    instructions = [
        "↑↓: Navigate items  PgUp/PgDn: Scroll page",
        "ENTER: Purchase item  📢 ESC: Return to game"
    ]

    instruction_y = self.HEIGHT - 50
    for i, instruction in enumerate(instructions):
        color = MENU_SELECTED if "ESC" in instruction else WHITE
        instruction_surface = self.ui_renderer.small_font.render(instruction, True, color)
        instruction_rect = instruction_surface.get_rect(center=(self.WIDTH // 2, instruction_y))
        self.screen.blit(instruction_surface, instruction_rect)
        instruction_y += 18

    # Item counter
    counter_text = f"Item {self.store.selected_item + 1} of {max_items}"
    counter_surface = pygame.font.Font(None, 16).render(counter_text, True, MENU_TEXT)
    self.screen.blit(counter_surface, (650, 100))