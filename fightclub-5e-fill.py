#!/usr/local/bin/python3
import csv
from fdfgen import forge_fdf
import os
import sys
import xml.etree.ElementTree as ET
import re

sys.path.insert(0, os.getcwd())
filename_prefix = "NVC"
name = "Hobb Filth"
xml_file = name + ".xml"
pdf_file = "Blank_Character_Sheet.pdf"
tmp_file = "tmp.fdf"
output_folder = './output/'
player_name = 'CodedWrench'
alignment = 'Chaotic Good'
armor = 0
armor_type = 0

def add_xml_data(field_name, xml_find_string):
  global fields, xml
  print(field_name)
  print(xml_find_string)
  fields[field_name] = xml.find(xml_find_string).text

def add_custom_data(field_name, data):
  global fields
  fields[field_name] = data

def append_custom_data(field_name, data, delimiter):
  global fields
  fields[field_name]+=delimiter+data

def character_info(xml):
  global level, player_class
  # TODO: multiclass support
  # hack: <level> node is missing for level 1s.
  level = str(xml.find('./character/class/level').text) if not xml.find('./character/class/level') == None else 1
  player_class = str(xml.find('./character/class/name').text)
  
  add_custom_data('ClassLevel','Level ' + str(level) + ' ' + player_class)
  add_custom_data('PlayerName',player_name)
  add_custom_data('Alignment',alignment)

def background_info(xml):
  personality = xml.find('./character/background/personality')
  ideals = xml.find('./character/background/ideals')
  bonds = xml.find('./character/background/bonds')
  flaws = xml.find('./character/background/flaws')

  personality = (personality.text if personality is not None else '')
  ideals = (ideals.text if ideals is not None else '')
  bonds = (bonds.text if bonds is not None else '')
  flaws = (flaws.text if flaws is not None else '')
      
  add_custom_data('PersonalityTraits ', personality)
  add_custom_data('Ideals', ideals)
  add_custom_data('Bonds', bonds)
  add_custom_data('Flaws', flaws)

  feats = xml.findall('./character/background/feat')
  feats_text = ""
  for feat in feats:
    feats_text += feat.find('name').text+"\r\n"
    feats_text += feat.find('text').text+"\r\n"

  add_custom_data('Feat+Traits',feats_text)


def combat_info(xml,ability_modifiers):
  add_custom_data('Initiative', ('+' if int(ability_modifiers[1]) >= 0 else '') + str(ability_modifiers[1]))
  #hack: speed is not included if default (30 ft)
  add_custom_data('Speed', '30 ft')

def ability_scores_and_modifiers(xml):
  abilities = xml.find('./character/abilities').text.split(',')
  ability_modifiers = []
  race_modifiers = xml.findall('./character/race/mod')

  for mod in race_modifiers:
    if mod.find('category').text == '1':
      # hack: Strength missing <type> node
      mod_index = int(mod.find('type').text) if not mod.find('type') == None else 0
      abilities[mod_index] = int(abilities[mod_index]) + int(mod.find('value').text)

  for i in range(0,6):
    ability_modifiers.append((int(abilities[i]) - 10) // 2)

  add_custom_data('STRmod', ('+' if ability_modifiers[0] >= 0 else '') + str(ability_modifiers[0]))
  add_custom_data('STR', abilities[0])
  add_custom_data('DEXmod ',('+' if ability_modifiers[1] >= 0 else '') + str(ability_modifiers[1]))
  add_custom_data('DEX', abilities[1])
  add_custom_data('CONmod', ('+' if ability_modifiers[2] >= 0 else '') + str(ability_modifiers[2]))
  add_custom_data('CON', abilities[2])
  add_custom_data('INTmod', ('+' if ability_modifiers[3] >= 0 else '') + str(ability_modifiers[3]))
  add_custom_data('INT', abilities[3])
  add_custom_data('WISmod', ('+' if ability_modifiers[4] >= 0 else '') + str(ability_modifiers[4]))
  add_custom_data('WIS', abilities[4])
  add_custom_data('CHamod', ('+' if ability_modifiers[5] >= 0 else '') + str(ability_modifiers[5]))
  add_custom_data('CHA', abilities[5])
  
  return ability_modifiers

def proficiency(level):
  proficiency_modifier = (int(level) - 1 )// 4 + 2
  add_custom_data('ProfBonus','+' + str(proficiency_modifier))
  return proficiency_modifier

def skill_modifiers(ability_modifiers,proficiency_modifier):

  # Skill Proficiencies
  skills = ('Acrobatics', 'Animal', 'Arcana', 'Athletics', 'Deception ',\
   'History ','Insight','Intimidation','Investigation ','Medicine','Nature',\
   'Perception ', 'Performance','Persuasion','Religion','SleightofHand','Stealth ','Survival')
  abilities_for_skills = (1,4,3,0,5,3,4,5,3,4,3,4,5,5,3,1,1,4)
  race_proficiencies = xml.findall('./character/race/proficiency')
  class_proficiencies = xml.findall('./character/class/proficiency')
  background_proficiencies = xml.findall('./character/background/proficiency')
  skill_modifiers = list(abilities_for_skills)
  other_skill_modifiers = [0] * len(abilities_for_skills)

  # Expertises for rogue (proficiency modifier gets added again to skill)
  feat_skill_expertises = xml.findall('./character/class/feat/mod')
  for skill_expertise in feat_skill_expertises:
      if skill_expertise.find('category').text == '4':
          skill = int(skill_expertise.find('type').text)
          other_skill_modifiers[skill] += int(proficiency_modifier)

  filled = []
  for i in range(0,len(skills)):
    for proficiency in race_proficiencies:
      if int(proficiency.text) - 100 == i:
        skill_modifiers[i] = str(int(ability_modifiers[abilities_for_skills[i]]) + int(proficiency_modifier) + other_skill_modifiers[i])
        add_custom_data(skills[i], ('+' if int(skill_modifiers[i]) >= 0 else '') + skill_modifiers[i])
        add_custom_data('Check Box ' + str(i+23),'Yes')
        filled.append(i)
    for proficiency in class_proficiencies:
      if int(proficiency.text) - 100 == i:
        skill_modifiers[i] = str(int(ability_modifiers[abilities_for_skills[i]]) + int(proficiency_modifier) + other_skill_modifiers[i])
        add_custom_data(skills[i], ('+' if int(skill_modifiers[i]) >= 0 else '') + skill_modifiers[i])        
        add_custom_data('Check Box ' + str(i+23),'Yes')
        filled.append(i)
    for proficiency in background_proficiencies:
      if int(proficiency.text) - 100 == i:
        skill_modifiers[i] = str(int(ability_modifiers[abilities_for_skills[i]]) + int(proficiency_modifier) + other_skill_modifiers[i])
        add_custom_data(skills[i], ('+' if int(skill_modifiers[i]) >= 0 else '') + skill_modifiers[i])        
        add_custom_data('Check Box ' + str(i+23),'Yes')
        filled.append(i)

  # skills without proficiency
  for i in range(0,len(skills)):
    if not i in filled:
        skill_modifiers[i] = str(int(ability_modifiers[abilities_for_skills[i]]) + other_skill_modifiers[i])
        add_custom_data(skills[i], ('+' if int(skill_modifiers[i]) >= 0 else '') + skill_modifiers[i])

  # passive perception
  add_custom_data('Passive',10 + int(skill_modifiers[11]))

def saving_throws(ability_modifiers,proficiency_modifier):
  #saving throws
  st_proficiencies = xml.findall('./character/class/proficiency')
  st_fields = ('ST Strength', 'ST Dexterity', 'ST Constitution', 'ST Intelligence','ST Wisdom','ST Charisma')
  st_filled = []
  for i in range(0,len(st_fields)):
    for proficiency in st_proficiencies:
      if int(proficiency.text) == i:
        add_custom_data(st_fields[i], '+' + str(int(ability_modifiers[i]) + int(proficiency_modifier)))
        if i == 0:
          add_custom_data('Check Box 11','Yes')
        else:
          add_custom_data('Check Box ' + str(i+17),'Yes')
        st_filled.append(i)

  for i in range(0,len(st_fields)):
    if not i in st_filled:
      add_custom_data(st_fields[i], ('+' if ability_modifiers[i] >=0 else '') + str(ability_modifiers[i]))

def features_and_traits(xml):
  # Feat+Traits - page 2
  age = xml.find('./character/race/age')
  height = xml.find('./character/race/height')
  weight = xml.find('./character/race/weight')
  eyes = xml.find('./character/race/eyes')
  skin = xml.find('./character/race/skin')
  hair = xml.find('./character/race/hair')
      
  add_custom_data('Age', age.text)
  add_custom_data('Height', height.text)
  add_custom_data('Weight', weight.text)
  add_custom_data('Eyes', eyes.text)
  add_custom_data('Skin', skin.text)
  add_custom_data('Hair', hair.text)

  all_speed_modifier = 0
  speed_change_applied = False

  feat_text = ''
  feats = xml.findall('./character/class/feat') + xml.findall('./character/feat') + xml.findall('./character/race/feat')

  # Double loop this because we need this info in the next loop
  for feat in feats:
    # speed modifiers
    mods = feat.findall('mod')
    for mod in mods:
        mod_type = mod.find('type')
        if mod_type is not None and mod_type.text == '13':
            all_speed_modifier += int(mod.find('value').text)

  if (all_speed_modifier > 0):
      add_custom_data('Speed', "{} ft".format(30 + all_speed_modifier))

  for feat in feats:
    # hack: speed feats
    if 'Speed' in feat.find('name').text:
      # Group 1 captures words that end double-letter ing, group 3 captures words that just end in ing
      speed_type = re.findall(r'([a-z]*([a-z]))\2{1}ing|([a-z]*)ing',feat.find('text').text)
      append_custom_data('Speed',str(int(re.findall(r"[0-9]+",feat.find('text').text)[0]) + all_speed_modifier) +'ft (' + (speed_type[0][0] if speed_type[0][0] else speed_type[0][2]) + ')',' /\r\n')
      speed_change_applied = True

    # hack: language proficiencies
    elif 'Languages' in feat.find('name').text:
      add_custom_data('ProficienciesLang',feat.find('text').text)

    else:
      feat_text+= feat.find('name').text + ':\r\n' + feat.find('text').text.replace('•','\r\n•')+"\r\n"


  add_custom_data('Features and Traits',feat_text.strip())

def damage_type_num_to_text(damage_type):
    # TODO: Find out what the other types are
    if damage_type == 1:
        return "B"
    if damage_type == 2:
        return "P"
    if damage_type == 3:
        return "S"

def index_to_weapon_fields(index):
    if index == 0: 
        return ["Wpn Name", "Wpn1 Damage", "Wpn1 AtkBonus"]
    elif index == 1: 
        return ["Wpn Name 2", "Wpn2 Damage ", "Wpn2 AtkBonus "]
    elif index == 2: 
        return ["Wpn Name 3", "Wpn3 Damage ", "Wpn3 AtkBonus  "]


def treasure(xml, ability_modifiers, proficiency_modifier):
  # Treasure - page 2
  item_text = ''
  ammunition_text = ''
  armor_text = ''
  equipment_text = ''
  weapon_index = 0

  treasure = xml.findall('./character/item')
  for item in treasure:
      slot = item.find('slot')
      damageType = item.find('damageType')

      # hack: money
      if item.find('name').text == "Copper (cp)":
        add_custom_data('CP',item.find('quantity').text)
      elif item.find('name').text == "Silver (sp)":
        add_custom_data('SP',item.find('quantity').text)
      elif item.find('name').text == "Electrum (ep)":
        add_custom_data('EP',item.find('quantity').text)
      elif item.find('name').text == "Gold (gp)":
        add_custom_data('GP',item.find('quantity').text)
      elif item.find('name').text == "Platinum (pp)":
        add_custom_data('PP',item.find('quantity').text)
      # Equipped ammunition
      elif slot is not None and slot.text == '1':
        item_amount = item.find('quantity')
        if item_amount is not None:
            item_amount = item_amount.text
        else:
            item_amount = '1'

        if int(item_amount) > 1:
            ammunition_text += "({}x) ".format(item_amount) 

        ammunition_text += item.find('name').text  + ", "
      # Weapon 
      elif damageType is not None and weapon_index <= 2:
        weapon_pdf_fields = index_to_weapon_fields(weapon_index)
        weapon_text = ''
        damage_text = ''
        attack_bonus_text = ''
        item_amount = item.find('quantity')

        ## Attack Bonus
        # TODO: Take weapon proficiency into account?
        # Hack (Finesse, probably attainable in weaponProperty or something)
        finesse = item.find('text').text.find("Finesse") != -1 
        ranged_weapon = item.find('type').text == '6'
        if (ranged_weapon):
            skill_modifier = ability_modifiers[1]
        elif (finesse):
            skill_modifier = max(ability_modifiers[0], ability_modifiers[1])
        else:
            skill_modifier = ability_modifiers[0]

        attack_bonus_text = "{0:+g}".format(skill_modifier + proficiency_modifier)

        ## Damage
        damage_1h = item.find('damage1H')
        damage_2h = item.find('damage2H')
        if damage_1h is not None:
          damage_text += damage_1h.text
        if damage_2h is not None:
            damage_text += "/" + damage_2h.text

        damage_text += "{0:+g}".format(skill_modifier)
        damage_text += damage_type_num_to_text(int(item.find('damageType').text))

        short_range = item.find('weaponRange')
        long_range = item.find('weaponLongRange')

        if short_range is not None:
            damage_text += " "  + short_range.text
        if long_range is not None:
            damage_text += "/" + long_range.text

        ## Amount
        if item_amount is not None:
            item_amount = item_amount.text
        else:
            item_amount = '1'

        if int(item_amount) > 1:
            weapon_text += "({}x) ".format(item_amount) 

        weapon_text += item.find('name').text 

        add_custom_data(weapon_pdf_fields[0],weapon_text.strip())
        add_custom_data(weapon_pdf_fields[1],damage_text.strip())
        add_custom_data(weapon_pdf_fields[2],attack_bonus_text.strip())

        weapon_index += 1
      # Equipped armor
      elif slot is not None and slot.text == '5':
        armor_text += item.find('name').text  + ", "
        global armor
        armor = int(item.find('ac').text)
        global armor_type
        armor_type = int(item.find('type').text)

      else:
        item_amount = item.find('quantity')
        if item_amount is not None:
            item_amount = item_amount.text
        else:
            item_amount = '1'

        if int(item_amount) > 1:
            item_text += "({}x) ".format(item_amount) 
        item_text += item.find('name').text  + ", "

  item_text = item_text[:-2]
  armor_text = armor_text[:-2]
  add_custom_data('Treasure',item_text.strip())

  equipment_text = ammunition_text + armor_text 
  add_custom_data('Equipment', equipment_text.strip())

def armor_class(xml, ability_modifiers):
    # TODO: Shield
    # TODO: Special class ACs and such (Unarmored defence, monks)
    # TODO: Disadvantages?
    armor_class = 10

    if armor != 0:
        if armor_type == 1:
            # type 1 light armor
            armor_class = armor + ability_modifiers[1]
        elif armor_type == 2:
            # type 2 medium armor (max dex 2)
            dex_mod = min(2, ability_modifiers[1])
            armor_class = armor + dex_mod
        else:
            # type 3 heavy armor (no dex mod) 
            armor_class = armor
    else:
        armor_class = 10 + ability_modifiers[1]

    add_custom_data('AC', armor_class)


def hit_die_type_to_dice_type(hit_die_type):
    if hit_die_type == "2":
        return "d8"
    if hit_die_type == "3":
        return "d10"
    elif hit_die_type == "4":
        return "d12"

    return "d6"


def hit_die(xml):
    hit_die_text = ''

    character_classes = xml.findall('./character/class')
    for character_class in character_classes:
        level = character_class.find('level')
        hd = character_class.find('hd')

        if hd == None:
            hd = "1"
        else:
            hd = hd.text

        if level == None:
            level = "1"
        else:
            level = level.text

        hit_die_text = level + hit_die_type_to_dice_type(hd) + " + "

    hit_die_text = hit_die_text[:3]
    add_custom_data('HDTotal', hit_die_text.strip())


def simple_fields(xml):
  with open('simple-field-mapping.csv', newline='') as csvfile:
    spamreader = csv.DictReader(csvfile, delimiter=',', quotechar='|')
    for row in spamreader:
      add_xml_data(row['field'], row['path'])

def process_xml(file):
  global fields, xml, level
  fields = {}

  with open(file, 'r') as xml_file:
    data=xml_file.read().replace('\n', '')
    xml=ET.fromstring(data)

  # must be first because level is calculated
  character_info(xml)


  proficiency_modifier = proficiency(level)

  simple_fields(xml)
  background_info(xml)
  ability_modifiers = ability_scores_and_modifiers(xml)
  combat_info(xml,ability_modifiers)
  skill_modifiers(ability_modifiers,proficiency_modifier)
  saving_throws(ability_modifiers,proficiency_modifier)
  # TODO: Add all feats, not just first. Can work out how many per page based on length.
  # TODO: Calculate bonuses given from feats.
  features_and_traits(xml)
  treasure(xml, ability_modifiers, proficiency_modifier)
  armor_class(xml, ability_modifiers)
  hit_die(xml)


def form_fill(fields):

  fdf = forge_fdf("",fields,[],[],[])
  fdf_file = open(tmp_file,"wb")
  fdf_file.write(fdf)
  fdf_file.close()
  output_file = '{0}{1}.pdf'.format(output_folder, name)
  cmd = 'pdftk "{0}" fill_form "{1}" output "{2}" dont_ask'.format(pdf_file, tmp_file, output_file)
  #print(cmd)
  os.system(cmd)
  os.remove(tmp_file)

process_xml(xml_file)
form_fill(fields)
