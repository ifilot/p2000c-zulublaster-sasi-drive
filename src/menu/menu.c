/* SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors */
/* SPDX-License-Identifier: GPL-3.0-or-later */

/**
 * @file menu.c
 * @brief Text-mode CP/M program navigator for the Philips P2000C.
 *
 * The program reads host-compiled menu data, displays cascading category and
 * application menus, provides a screen saver, and replaces itself with the
 * selected CP/M COM program. Build it with Z88DK's classic +cpm library.
 */

#include <cpm.h>
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Configuration limits. */
#define MAX_ITEMS 32
#define MAX_CATEGORIES 8
#define MAX_CATEGORY_ITEMS 14
#define MAX_LABEL_LENGTH 24
#define MAX_PROGRAM_LENGTH 8
#define MAX_ARGUMENT_LENGTH 100
#define MAX_DESCRIPTION_LENGTH 200
#define MAX_TITLE_LENGTH 48

/* P2000C table glyphs used to draw the menu windows. */
#define TABLE_TOP_LEFT 0xa9
#define TABLE_BOTTOM_LEFT 0xaa
#define TABLE_TOP_RIGHT 0xb9
#define TABLE_BOTTOM_RIGHT 0xba
#define TABLE_HORIZONTAL 0xd0
#define TABLE_VERTICAL 0xfa

/* Screen layout. */
#define SCREEN_WIDTH 80
#define DESCRIPTION_COLUMN 3
#define DESCRIPTION_ROW 1
#define DESCRIPTION_WIDTH 74
#define DESCRIPTION_LINES 3
#define MENU_ROW 5
#define CATEGORY_COLUMN 3
#define CATEGORY_WIDTH 18
#define PROGRAM_COLUMN 24
#define PROGRAM_WIDTH 32
#define STATUS_ROW 21
#define FOOTER_ROW 23
#define FOOTER_WIDTH 79

/* Terminal attributes. */
#define ATTRIBUTE_DIM 0x01
#define ATTRIBUTE_NORMAL 0x40
#define ATTRIBUTE_INVERSE 0x50

/* Configuration and presentation text. */
#define CONFIG_PATH "0/A:MENU.DAT"
#define DATA_FORMAT_VERSION 1
#define DEFAULT_TITLE "P2000C NAVIGATOR"
#define DEFAULT_FOOTER "Home Computer Museum"
#define SAVER_TEXT "P2000C - druk op een toets"
#define DEFAULT_SAVER_SECONDS 120
#define SAVER_TICKS_PER_SECOND 100

#ifndef NAVIGATOR_VERSION
#define NAVIGATOR_VERSION "onbekend"
#endif
#ifndef NAVIGATOR_BUILD_DATE
#define NAVIGATOR_BUILD_DATE "onbekend"
#endif

/*
 * Real P2000C cursor keys emit Ctrl-S/D/E/X navigation codes. The
 * graphical emulator emits terminal cursor-control bytes, so both are valid.
 */
#define KEY_LEFT 0x13
#define KEY_RIGHT 0x04
#define KEY_UP 0x05
#define KEY_DOWN 0x18
#define KEY_LEFT_ALT 0x15
#define KEY_RIGHT_ALT 0x06
#define KEY_UP_ALT 0x1a
#define KEY_DOWN_ALT 0x0a

/** A configured CP/M application. */
typedef struct {
  char label[MAX_LABEL_LENGTH + 1];
  char program[MAX_PROGRAM_LENGTH + 1];
  char args[MAX_ARGUMENT_LENGTH + 1];
  char description[MAX_DESCRIPTION_LENGTH + 1];
  unsigned char drive;
  unsigned char user;
  unsigned char category;
} MenuEntry;

/** A named menu category and its explanatory text. */
typedef struct {
  char label[MAX_LABEL_LENGTH + 1];
  char description[MAX_DESCRIPTION_LENGTH + 1];
} MenuCategory;

/* Parsed menu state. */
static MenuEntry entries[MAX_ITEMS];
static MenuCategory categories[MAX_CATEGORIES];
static unsigned char entry_count;
static unsigned char category_count;
static unsigned char selected_category;
static unsigned char selected_program;
static unsigned char program_focus;

/* CP/M state restored when Navigator exits or a launch fails. */
static unsigned char home_drive;
static unsigned char home_user;

/* Configuration values and binary input state. */
static unsigned int saver_seconds = DEFAULT_SAVER_SECONDS;
static char title[MAX_TITLE_LENGTH + 1] = DEFAULT_TITLE;
static char footer[MAX_TITLE_LENGTH + 1] = DEFAULT_FOOTER;
static char status[77];
static unsigned int data_remaining;
static unsigned int data_crc;

/*
 * These values are public because the assembly trampoline copies them after
 * the C program and its stack have become disposable.
 */
unsigned char launch_fcb[36];
unsigned int launch_records;

/**
 * @brief Replaces Navigator with the selected COM program.
 *
 * This assembly routine does not return after its first successful disk read.
 */
extern void chain_program(void);

/**
 * @brief Waits for one calibrated polling tick on a 4 MHz P2000C.
 */
extern void idle_tick(void);

/** Configures warm boot for an intentional Navigator exit to the CCP. */
extern void set_menu_warm_boot(void);

/** Configures the launched program returning by warm boot to restart Navigator.
 */
extern void set_program_warm_boot(void);

/* ------------------------------------------------------------------------- */
/* Terminal output.                                                          */
/* ------------------------------------------------------------------------- */

/**
 * @brief Writes one byte through the CP/M direct-console service.
 *
 * @param character Byte to write to the terminal.
 */
static void write_console(unsigned char character) {
  bdos(CPM_DCIO, character);
}

/**
 * @brief Writes a null-terminated string to the terminal.
 *
 * @param text String to write.
 */
static void write_text(const char *text) {
  while (*text) {
    write_console(*text++);
  }
}

/**
 * @brief Writes a two-byte P2000C escape sequence.
 *
 * @param command Character following ESC.
 */
static void write_escape(char command) {
  write_console(27);
  write_console(command);
}

/**
 * @brief Moves the cursor to a zero-based screen position.
 *
 * @param row Zero-based terminal row.
 * @param column Zero-based terminal column.
 */
static void move_cursor(unsigned char row, unsigned char column) {
  write_escape('Y');
  write_console(row + 32);
  write_console(column + 32);
}

/**
 * @brief Selects a P2000C character attribute.
 *
 * @param attribute P2000C attribute byte.
 */
static void set_attribute(unsigned char attribute) {
  write_escape('0');
  write_console(attribute);
}

/**
 * @brief Clears the text screen and hides the cursor.
 */
static void clear_screen(void) {
  set_attribute(ATTRIBUTE_NORMAL);
  write_console(12);
  write_escape('c');
}

/**
 * @brief Writes text padded or clipped to an exact field width.
 *
 * @param text Text to place in the field.
 * @param width Number of character cells to write.
 */
static void write_field(const char *text, unsigned char width) {
  while (width--) {
    write_console(*text ? *text++ : ' ');
  }
}

/**
 * @brief Draws a horizontal border with native P2000C table glyphs.
 *
 * @param row Zero-based row of the border.
 * @param column Zero-based column of the left corner.
 * @param left Left-corner glyph.
 * @param right Right-corner glyph.
 * @param width Number of horizontal glyphs between the corners.
 */
static void draw_frame_line(unsigned char row, unsigned char column,
                            unsigned char left, unsigned char right,
                            unsigned char width) {
  move_cursor(row, column);
  write_console(left);
  while (width--) {
    write_console(TABLE_HORIZONTAL);
  }
  write_console(right);
}

/**
 * @brief Draws a rectangular panel using native P2000C table glyphs.
 */
static void draw_frame_box(unsigned char top, unsigned char bottom,
                           unsigned char column, unsigned char width) {
  unsigned char row;

  draw_frame_line(top, column, TABLE_TOP_LEFT, TABLE_TOP_RIGHT, width);
  for (row = top + 1; row < bottom; ++row) {
    move_cursor(row, column);
    write_console(TABLE_VERTICAL);
    move_cursor(row, column + width + 1);
    write_console(TABLE_VERTICAL);
  }
  draw_frame_line(bottom, column, TABLE_BOTTOM_LEFT, TABLE_BOTTOM_RIGHT, width);
}

/**
 * @brief Draws a centered inverse-video bar.
 *
 * @param row Zero-based screen row.
 * @param label Text centered in the bar.
 * @param width Width of the bar in character cells.
 */
static void draw_bar(unsigned char row, const char *label,
                     unsigned char width) {
  unsigned char left_padding;
  unsigned char label_length;

  label_length = strlen(label);
  left_padding = (width - label_length) / 2;
  move_cursor(row, 0);
  set_attribute(ATTRIBUTE_INVERSE);
  write_field("", left_padding);
  write_text(label);
  write_field("", width - left_padding - label_length);
  set_attribute(ATTRIBUTE_NORMAL);
}

/* ------------------------------------------------------------------------- */
/* Menu model lookups.                                                       */
/* ------------------------------------------------------------------------- */

/**
 * @brief Counts the applications assigned to one category.
 *
 * @param category Category index to inspect.
 * @return Number of applications in the category.
 */
static unsigned char count_category_programs(unsigned char category) {
  unsigned char index;
  unsigned char total;

  total = 0;
  for (index = 0; index < entry_count; ++index) {
    if (entries[index].category == category) {
      ++total;
    }
  }
  return total;
}

/**
 * @brief Finds an application by its ordinal position in a category.
 *
 * @param category Category index to search.
 * @param ordinal Zero-based application position within the category.
 * @return Pointer to the application, or NULL when it does not exist.
 */
static MenuEntry *find_category_program(unsigned char category,
                                        unsigned char ordinal) {
  unsigned char index;

  for (index = 0; index < entry_count; ++index) {
    if (entries[index].category == category && ordinal-- == 0) {
      return &entries[index];
    }
  }
  return NULL;
}

/* ------------------------------------------------------------------------- */
/* Binary menu data.                                                         */
/* ------------------------------------------------------------------------- */

/**
 * @brief Adds one byte to the CRC-16/CCITT-FALSE checksum.
 *
 * @param value Byte to include.
 */
static void update_data_crc(unsigned char value) {
  unsigned char bit;

  data_crc ^= (unsigned int)value << 8;
  for (bit = 0; bit < 8; ++bit) {
    if (data_crc & 0x8000) {
      data_crc = (data_crc << 1) ^ 0x1021;
    } else {
      data_crc <<= 1;
    }
  }
}

/**
 * @brief Reads one checksummed byte from the declared payload.
 *
 * @param file Open binary MENU.DAT stream.
 * @return Byte value, or -1 on truncation or over-read.
 */
static int read_data_byte(FILE *file) {
  int value;

  if (!data_remaining) {
    return -1;
  }
  value = fgetc(file);
  if (value == EOF) {
    return -1;
  }
  --data_remaining;
  update_data_crc((unsigned char)value);
  return value;
}

/**
 * @brief Reads and validates a printable ASCII string from the payload.
 *
 * @param file Open binary MENU.DAT stream.
 * @param destination Destination buffer.
 * @param length Encoded string length.
 * @param maximum Largest length accepted by the destination.
 * @param allow_empty Whether a zero-length string is valid.
 * @return Nonzero when the complete string is valid.
 */
static int read_data_string(FILE *file, char *destination, unsigned char length,
                            unsigned char maximum, unsigned char allow_empty) {
  unsigned char index;
  int value;

  if (length > maximum || (!allow_empty && !length)) {
    return 0;
  }
  for (index = 0; index < length; ++index) {
    value = read_data_byte(file);
    if (value < 32 || value > 126) {
      return 0;
    }
    destination[index] = value;
  }
  destination[length] = 0;
  return 1;
}

/**
 * @brief Restores safe defaults after invalid binary menu data.
 */
static void reject_menu_data(void) {
  entry_count = 0;
  category_count = 0;
  selected_category = 0;
  selected_program = 0;
  program_focus = 0;
  saver_seconds = DEFAULT_SAVER_SECONDS;
  strcpy(title, DEFAULT_TITLE);
  strcpy(footer, DEFAULT_FOOTER);
  strcpy(status, "MENU.DAT is ongeldig. Bouw de menugegevens opnieuw.");
}

/**
 * @brief Resets menu state and reads versioned MENU.DAT from A: user 0.
 */
static void load_config(void) {
  unsigned char header[16];
  unsigned char expected_categories;
  unsigned char expected_entries;
  unsigned char title_length;
  unsigned char footer_length;
  unsigned char category_index;
  unsigned char program_index;
  unsigned char category_programs;
  unsigned char label_length;
  unsigned char description_length;
  unsigned char program_length;
  unsigned char argument_length;
  unsigned char reserved;
  unsigned int expected_crc;
  int drive;
  int user;
  FILE *file;
  MenuCategory *category;
  MenuEntry *entry;

  entry_count = 0;
  category_count = 0;
  selected_category = 0;
  selected_program = 0;
  program_focus = 0;
  saver_seconds = DEFAULT_SAVER_SECONDS;
  strcpy(title, DEFAULT_TITLE);
  strcpy(footer, DEFAULT_FOOTER);
  status[0] = 0;

  file = fopen(CONFIG_PATH, "rb");
  if (!file) {
    strcpy(status,
           "Kan A:MENU.DAT (gebruiker 0) niet openen. H: hulp   Q: CP/M");
    return;
  }
  if (fread(header, 1, sizeof(header), file) != sizeof(header) ||
      header[0] != 'P' || header[1] != '2' || header[2] != 'M' ||
      header[3] != 'N' || header[4] != DATA_FORMAT_VERSION || header[7] ||
      !header[5] || header[5] > MAX_CATEGORIES || !header[6] ||
      header[6] > MAX_ITEMS) {
    fclose(file);
    reject_menu_data();
    return;
  }

  expected_categories = header[5];
  expected_entries = header[6];
  saver_seconds = header[8] | (unsigned int)header[9] << 8;
  data_remaining = header[10] | (unsigned int)header[11] << 8;
  expected_crc = header[12] | (unsigned int)header[13] << 8;
  title_length = header[14];
  footer_length = header[15];
  data_crc = 0xffff;
  if ((saver_seconds > 0 && saver_seconds < 5) || saver_seconds > 3600 ||
      !read_data_string(file, title, title_length, MAX_TITLE_LENGTH, 0) ||
      !read_data_string(file, footer, footer_length, MAX_TITLE_LENGTH, 0)) {
    fclose(file);
    reject_menu_data();
    return;
  }

  for (category_index = 0; category_index < expected_categories;
       ++category_index) {
    label_length = read_data_byte(file);
    description_length = read_data_byte(file);
    category_programs = read_data_byte(file);
    reserved = read_data_byte(file);
    if (!category_programs || category_programs > MAX_CATEGORY_ITEMS ||
        reserved || entry_count + category_programs > expected_entries) {
      fclose(file);
      reject_menu_data();
      return;
    }
    category = &categories[category_index];
    if (!read_data_string(file, category->label, label_length, MAX_LABEL_LENGTH,
                          0) ||
        !read_data_string(file, category->description, description_length,
                          MAX_DESCRIPTION_LENGTH, 1)) {
      fclose(file);
      reject_menu_data();
      return;
    }
    ++category_count;

    for (program_index = 0; program_index < category_programs;
         ++program_index) {
      label_length = read_data_byte(file);
      program_length = read_data_byte(file);
      argument_length = read_data_byte(file);
      description_length = read_data_byte(file);
      drive = read_data_byte(file);
      user = read_data_byte(file);
      if (drive < 0 || drive > 6 || user < 0 || user > 15) {
        fclose(file);
        reject_menu_data();
        return;
      }
      entry = &entries[entry_count];
      if (!read_data_string(file, entry->label, label_length, MAX_LABEL_LENGTH,
                            0) ||
          !read_data_string(file, entry->program, program_length,
                            MAX_PROGRAM_LENGTH, 0) ||
          !read_data_string(file, entry->args, argument_length,
                            MAX_ARGUMENT_LENGTH, 1) ||
          !read_data_string(file, entry->description, description_length,
                            MAX_DESCRIPTION_LENGTH, 1)) {
        fclose(file);
        reject_menu_data();
        return;
      }
      entry->drive = drive;
      entry->user = user;
      entry->category = category_index;
      ++entry_count;
    }
  }
  fclose(file);
  if (entry_count != expected_entries ||
      category_count != expected_categories || data_remaining ||
      data_crc != expected_crc) {
    reject_menu_data();
  }
}

/* ------------------------------------------------------------------------- */
/* Menu rendering.                                                           */
/* ------------------------------------------------------------------------- */

/**
 * @brief Draws one row in the category window.
 *
 * @param index Category index to draw.
 */
static void draw_category_row(unsigned char index) {
  move_cursor(MENU_ROW + 1 + index, CATEGORY_COLUMN);
  set_attribute(ATTRIBUTE_NORMAL);
  write_console(TABLE_VERTICAL);
  set_attribute(index == selected_category ? ATTRIBUTE_INVERSE
                                           : ATTRIBUTE_NORMAL);
  write_field(categories[index].label, CATEGORY_WIDTH - 2);
  write_text(" >");
  set_attribute(ATTRIBUTE_NORMAL);
  write_console(TABLE_VERTICAL);
}

/**
 * @brief Draws one row in the application window.
 *
 * @param index Application ordinal within the selected category.
 * @param selected Nonzero to draw the row in inverse video.
 */
static void draw_program_row(unsigned char index, unsigned char selected) {
  MenuEntry *entry;

  entry = find_category_program(selected_category, index);
  move_cursor(MENU_ROW + 1 + index, PROGRAM_COLUMN);
  set_attribute(ATTRIBUTE_NORMAL);
  write_console(TABLE_VERTICAL);
  set_attribute(selected ? ATTRIBUTE_INVERSE : ATTRIBUTE_NORMAL);
  write_field(entry->label, PROGRAM_WIDTH);
  set_attribute(ATTRIBUTE_NORMAL);
  write_console(TABLE_VERTICAL);
}

/**
 * @brief Draws the selected category or application description.
 *
 * Category text is shown while the category window has focus. Application text
 * replaces it only after the user enters the application window.
 */
static void draw_description(void) {
  unsigned char row;
  unsigned char take;
  unsigned char shown;
  const char *source;
  char buffer[DESCRIPTION_WIDTH + 1];
  MenuEntry *entry;

  entry = find_category_program(selected_category, selected_program);
  source = categories[selected_category].description;
  if (program_focus && entry) {
    source = entry->description;
  }

  set_attribute(ATTRIBUTE_NORMAL);
  for (row = 0; row < DESCRIPTION_LINES; ++row) {
    move_cursor(DESCRIPTION_ROW + row, DESCRIPTION_COLUMN);
    write_field("", DESCRIPTION_WIDTH);
  }

  for (row = 0; row < DESCRIPTION_LINES; ++row) {
    while (*source == ' ') {
      ++source;
    }
    take =
        strlen(source) > DESCRIPTION_WIDTH ? DESCRIPTION_WIDTH : strlen(source);
    if (source[take] && take == DESCRIPTION_WIDTH) {
      while (take && source[take] != ' ') {
        --take;
      }
      if (!take) {
        take = DESCRIPTION_WIDTH;
      }
    }

    memcpy(buffer, source, take);
    buffer[take] = 0;
    shown = take;
    while (shown && buffer[shown - 1] == ' ') {
      buffer[--shown] = 0;
    }
    move_cursor(DESCRIPTION_ROW + row,
                DESCRIPTION_COLUMN + (DESCRIPTION_WIDTH - shown) / 2);
    write_text(buffer);
    source += take;
  }
}

/**
 * @brief Redraws the application window for the selected category.
 */
static void draw_program_panel(void) {
  unsigned char index;
  unsigned char programs;

  programs = count_category_programs(selected_category);
  set_attribute(ATTRIBUTE_NORMAL);
  for (index = 0; index < MAX_CATEGORY_ITEMS + 2; ++index) {
    move_cursor(MENU_ROW + index, PROGRAM_COLUMN);
    write_field("", PROGRAM_WIDTH + 2);
  }

  draw_frame_line(MENU_ROW, PROGRAM_COLUMN, TABLE_TOP_LEFT, TABLE_TOP_RIGHT,
                  PROGRAM_WIDTH);
  for (index = 0; index < programs; ++index) {
    draw_program_row(index, program_focus && index == selected_program);
  }
  draw_frame_line(MENU_ROW + programs + 1, PROGRAM_COLUMN, TABLE_BOTTOM_LEFT,
                  TABLE_BOTTOM_RIGHT, PROGRAM_WIDTH);
  draw_description();
}

/**
 * @brief Draws either the current status message or the navigation hints.
 */
static void draw_status_line(void) {
  move_cursor(STATUS_ROW, DESCRIPTION_COLUMN);
  set_attribute(ATTRIBUTE_NORMAL);
  if (*status) {
    write_field(status, DESCRIPTION_WIDTH);
  } else {
    write_field(
        "Omhoog/Omlaag kiezen  Rechts/ENTER openen  Links terug  Q afsluiten",
        DESCRIPTION_WIDTH);
  }
}

/**
 * @brief Redraws the complete Navigator screen.
 */
static void draw_menu(void) {
  unsigned char index;

  clear_screen();
  set_attribute(ATTRIBUTE_NORMAL);
  draw_bar(0, title, SCREEN_WIDTH);
  draw_bar(FOOTER_ROW, footer, FOOTER_WIDTH);

  if (!category_count) {
    move_cursor(10, 4);
    write_text(*status ? status : "Geen menucategorieen ingesteld.");
    return;
  }

  draw_frame_line(MENU_ROW, CATEGORY_COLUMN, TABLE_TOP_LEFT, TABLE_TOP_RIGHT,
                  CATEGORY_WIDTH);
  for (index = 0; index < category_count; ++index) {
    draw_category_row(index);
  }
  draw_frame_line(MENU_ROW + category_count + 1, CATEGORY_COLUMN,
                  TABLE_BOTTOM_LEFT, TABLE_BOTTOM_RIGHT, CATEGORY_WIDTH);

  draw_program_panel();
  draw_status_line();
}

/**
 * @brief Displays the keyboard help screen.
 */
static void draw_help(void) {
  clear_screen();
  draw_bar(0, title, SCREEN_WIDTH);
  draw_bar(FOOTER_ROW, footer, FOOTER_WIDTH);
  draw_frame_box(2, 12, 2, 74);
  move_cursor(2, 5);
  write_text(" BEDIENING ");
  draw_frame_box(14, 20, 2, 74);
  move_cursor(14, 5);
  write_text(" INFORMATIE ");
  move_cursor(3, 4);
  write_text("OMHOOG/OMLAAG of J/K kiest een onderdeel.");
  move_cursor(5, 4);
  write_text("RECHTS of ENTER opent een categorie. LINKS gaat terug.");
  move_cursor(7, 4);
  write_text("ENTER start het gekozen programma.");
  move_cursor(9, 4);
  write_text("S laadt de screensaver. Q sluit af.");
  move_cursor(11, 4);
  write_text("Na afloop van een programma keert Navigator automatisch terug.");
  move_cursor(15, 4);
  write_text("SASI-distributie: " NAVIGATOR_VERSION);
  move_cursor(17, 4);
  write_text("GitHub: github.com/ifilot/p2000c-zulublaster-sasi-drive");
  move_cursor(19, 4);
  write_text("Compilatiedatum: " NAVIGATOR_BUILD_DATE);
  move_cursor(21, 4);
  write_text("Druk op een toets om terug te keren.");
}

/* ------------------------------------------------------------------------- */
/* Keyboard input and screen saver.                                          */
/* ------------------------------------------------------------------------- */

/**
 * @brief Tests whether a key means move up.
 *
 * @param key Console byte to classify.
 * @return Nonzero for K or either supported Up code.
 */
static int is_up_key(int key) {
  return key == 'k' || key == 'K' || key == KEY_UP || key == KEY_UP_ALT;
}

/**
 * @brief Tests whether a key means move down.
 *
 * @param key Console byte to classify.
 * @return Nonzero for J or either supported Down code.
 */
static int is_down_key(int key) {
  return key == 'j' || key == 'J' || key == KEY_DOWN || key == KEY_DOWN_ALT;
}

/**
 * @brief Tests whether a key means move left.
 *
 * @param key Console byte to classify.
 * @return Nonzero for either supported Left code.
 */
static int is_left_key(int key) {
  return key == KEY_LEFT || key == KEY_LEFT_ALT;
}

/**
 * @brief Tests whether a key means move right.
 *
 * @param key Console byte to classify.
 * @return Nonzero for either supported Right code.
 */
static int is_right_key(int key) {
  return key == KEY_RIGHT || key == KEY_RIGHT_ALT;
}

/**
 * @brief Polls for a key while tracking the screen-saver timeout.
 *
 * CP/M 2.2 has no standard wall clock. One hundred calibrated 4 MHz delays,
 * plus BDOS and interrupt overhead, approximate one second.
 *
 * @return Console byte, or -1 when the screen saver should start.
 */
static int wait_for_key(void) {
  unsigned int seconds;
  unsigned char tick;
  int key;

  seconds = 0;
  tick = 0;
  for (;;) {
    key = bdos(CPM_DCIO, 255) & 255;
    if (key) {
      return key;
    }
    idle_tick();
    if (++tick == SAVER_TICKS_PER_SECOND) {
      tick = 0;
      if (saver_seconds && ++seconds >= saver_seconds) {
        return -1;
      }
    }
  }
}

/**
 * @brief Runs the moving text-mode screen saver until a key is pressed.
 *
 * Each movement clears the complete previous frame. This follows the
 * hardware-tested Othello saver and avoids remnants from partial overwrites.
 */
static void run_screen_saver(void) {
  unsigned char column;
  unsigned char row;
  unsigned char tick;

  column = 4;
  row = 3;
  tick = 0;
  clear_screen();
  set_attribute(ATTRIBUTE_DIM);
  move_cursor(row, column);
  write_text(SAVER_TEXT);

  while (!(bdos(CPM_DCIO, 255) & 255)) {
    idle_tick();
    if (++tick == SAVER_TICKS_PER_SECOND) {
      tick = 0;
      write_console(12);
      column = (column + 7) % 54;
      row = (row + 5) % 23;
      move_cursor(row, column);
      write_text(SAVER_TEXT);
    }
  }

  /* Consume queued wake-up input, including a repeated key. */
  while (bdos(CPM_DCIO, 255) & 255) {
  }
  set_attribute(ATTRIBUTE_NORMAL);
}

/**
 * @brief Asks the user to confirm returning to CP/M.
 *
 * @return Nonzero for confirmation; zero for cancellation or saver timeout.
 */
static int confirm_exit(void) {
  int key;

  move_cursor(STATUS_ROW, DESCRIPTION_COLUMN);
  set_attribute(ATTRIBUTE_INVERSE);
  write_field("Navigator afsluiten en terugkeren naar CP/M?  J/N",
              DESCRIPTION_WIDTH);
  set_attribute(ATTRIBUTE_NORMAL);

  for (;;) {
    key = wait_for_key();
    if (key == 'j' || key == 'J' || key == 'y' || key == 'Y') {
      return 1;
    }
    if (key == 'n' || key == 'N' || key == 'q' || key == 'Q' || key == 3 ||
        key == 27 || key == -1) {
      return 0;
    }
  }
}

/* ------------------------------------------------------------------------- */
/* CP/M program launch.                                                      */
/* ------------------------------------------------------------------------- */

/**
 * @brief Restores the drive, user area, and default DMA address.
 */
static void restore_cpm_environment(void) {
  bdos(CPM_SUID, home_user);
  bdos(CPM_LGIN, home_drive);
  bdos(CPM_SDMA, 0x80);
}

/**
 * @brief Builds one CP/M default FCB from the next command-line argument.
 *
 * @param fcb Destination FCB at 005Ch or 006Ch.
 * @param argument Address of the command-line cursor; advanced past one word.
 */
static void build_argument_fcb(unsigned char *fcb, char **argument) {
  unsigned char index;
  unsigned char limit;
  char *text;

  index = 1;
  limit = 9;
  text = *argument;
  memset(fcb, 0, 16);
  memset(fcb + 1, ' ', 11);

  while (*text == ' ' || *text == '\t') {
    ++text;
  }
  if (*text && text[1] == ':' && toupper(*text) >= 'A' &&
      toupper(*text) <= 'P') {
    fcb[0] = toupper(*text) - 'A' + 1;
    text += 2;
  }

  while (*text && *text != ' ' && *text != '\t') {
    if (*text == '.') {
      index = 9;
      limit = 12;
    } else if (*text == '*') {
      while (index < limit) {
        fcb[index++] = '?';
      }
    } else if (index < limit) {
      fcb[index++] = toupper(*text);
    }
    ++text;
  }
  *argument = text;
}

/**
 * @brief Prepares CP/M state and replaces Navigator with the selected program.
 *
 * On success, chain_program() overwrites the transient program area and never
 * returns. On validation or open failure, this function restores Navigator's
 * CP/M environment and records a Dutch status message.
 */
static void launch_selected_program(void) {
  MenuEntry *entry;
  unsigned int bdos_base;
  unsigned char *command_tail;
  char *arguments;
  unsigned int length;

  entry = find_category_program(selected_category, selected_program);
  bdos_base = *(unsigned int *)6;
  command_tail = (unsigned char *)0x80;
  arguments = entry->args;

  bdos(CPM_SUID, entry->user);
  bdos(CPM_LGIN, entry->drive);
  memset(launch_fcb, 0, sizeof(launch_fcb));
  memset(launch_fcb + 1, ' ', 11);
  memcpy(launch_fcb + 1, entry->program, strlen(entry->program));
  memcpy(launch_fcb + 9, "COM", 3);

  if ((bdos(CPM_OPN, (int)launch_fcb) & 255) == 255) {
    restore_cpm_environment();
    strcpy(status,
           "Programma niet gevonden. Controleer station, gebruiker en naam.");
    return;
  }

  bdos(CPM_CFS, (int)launch_fcb);
  launch_records = launch_fcb[33] | ((unsigned int)launch_fcb[34] << 8);

  /*
   * Standard CP/M 2.2 COM loading stops at the CCP, 2 KiB below BDOS.
   * Disposable scratch code is placed above that loading limit.
   */
  if (launch_fcb[35] || !launch_records ||
      launch_records > (bdos_base - 0x900) / 128) {
    bdos(CPM_CLS, (int)launch_fcb);
    restore_cpm_environment();
    strcpy(status, "Programma is leeg of te groot voor het CP/M-geheugen.");
    return;
  }

  memset((void *)0x5c, 0, 36);
  build_argument_fcb((unsigned char *)0x5c, &arguments);
  build_argument_fcb((unsigned char *)0x6c, &arguments);

  length = strlen(entry->args);
  *command_tail = length ? length + 1 : 0;
  if (length) {
    command_tail[1] = ' ';
    for (length = 0; entry->args[length]; ++length) {
      command_tail[length + 2] = toupper(entry->args[length]);
    }
  }
  command_tail[*command_tail + 1] = 13;

  /* Warm boot and programs consulting address 0004h see the selected drive. */
  *(unsigned char *)4 = (entry->user << 4) | entry->drive;
  clear_screen();
  write_escape('C');
  set_program_warm_boot();
  write_text("Start ");
  write_text(entry->label);
  write_text("...\r\n");
  chain_program();
}

/* ------------------------------------------------------------------------- */
/* Menu interaction.                                                        */
/* ------------------------------------------------------------------------- */

/**
 * @brief Handles a key while the application window has focus.
 *
 * @param key Console key to process.
 * @param programs Number of applications in the selected category.
 */
static void handle_program_key(int key, unsigned char programs) {
  unsigned char previous;

  if (is_left_key(key)) {
    previous = selected_program;
    program_focus = 0;
    draw_program_row(previous, 0);
    draw_description();
  } else if (key == 13) {
    launch_selected_program();
    draw_menu();
  } else if (is_down_key(key) && programs) {
    previous = selected_program;
    selected_program = (selected_program + 1) % programs;
    draw_program_row(previous, 0);
    draw_program_row(selected_program, 1);
    draw_description();
  } else if (is_up_key(key) && programs) {
    previous = selected_program;
    selected_program = selected_program ? selected_program - 1 : programs - 1;
    draw_program_row(previous, 0);
    draw_program_row(selected_program, 1);
    draw_description();
  }
}

/**
 * @brief Handles a key while the category window has focus.
 *
 * @param key Console key to process.
 * @param programs Number of applications in the selected category.
 */
static void handle_category_key(int key, unsigned char programs) {
  unsigned char previous;

  if (is_right_key(key) || key == 13) {
    if (programs) {
      program_focus = 1;
      draw_program_row(selected_program, 1);
      draw_description();
    }
  } else if (is_down_key(key)) {
    previous = selected_category;
    selected_category = (selected_category + 1) % category_count;
    selected_program = 0;
    draw_category_row(previous);
    draw_category_row(selected_category);
    draw_program_panel();
  } else if (is_up_key(key)) {
    previous = selected_category;
    selected_category =
        selected_category ? selected_category - 1 : category_count - 1;
    selected_program = 0;
    draw_category_row(previous);
    draw_category_row(selected_category);
    draw_program_panel();
  }
}

/**
 * @brief Runs the Navigator event loop until the user confirms exit.
 */
static void run_menu(void) {
  int key;
  unsigned char programs;

  for (;;) {
    key = wait_for_key();
    if (key == -1 || key == 's' || key == 'S') {
      run_screen_saver();
      draw_menu();
    } else if (key == 'q' || key == 'Q' || key == 3 || key == 27) {
      if (confirm_exit()) {
        return;
      }
      draw_menu();
    } else if (key == 'h' || key == 'H' || key == '?') {
      draw_help();
      if (wait_for_key() == -1) {
        run_screen_saver();
      }
      draw_menu();
    } else if (category_count) {
      programs = count_category_programs(selected_category);
      if (program_focus) {
        handle_program_key(key, programs);
      } else {
        handle_category_key(key, programs);
      }
    }
  }
}

/**
 * @brief Initializes Navigator, runs it, and restores CP/M on exit.
 *
 * @return Zero after the user returns to the CP/M command prompt.
 */
int main(void) {
  set_menu_warm_boot();
  home_drive = bdos(CPM_IDRV, 0);
  home_user = bdos(CPM_SUID, 255);

  write_escape('4');
  load_config();
  draw_menu();
  run_menu();

  restore_cpm_environment();
  clear_screen();
  write_escape('C');
  write_text(
      "CP/M is gereed. Typ USER 0 en daarna A:MENU om terug te keren.\r\n");
  return 0;
}
