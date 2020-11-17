# Minecraft-Programming-Language

This is a project that, when finished, will allow for the creation of data packs and data pack tags through a simple programming language syntax that resembles object oriented languages such as Java. This is intended to be much more powerful and user friendly than typing a series of commands like you do in regular development. Here are the planned features (checked features are implemented, while unchecked are works in progress):

 - [x] [Basic Use](#how-to-use)
 - [x] Tag Development
	 - [x] [Define a tag](#define-a-tag)
	 - [x] [Add entries to your tag](#add-entries)
	 - [x] [Remove entries from your tag](#remove-entries)
	 - [x] [Add comments to your tag](#tag-comments)
	 - [x] [Add entries from other tags](#specify-other-tags)
	 - [x] [Specify all available entries](#all)
	 - [x] [Filter entries by name](#filter-by-name)
	 - [x] [Filter entries by value](#filter-by-value)
	 - [x] [Sort entries](#sort)
	 - [x] [Limit entry count](#limit-count)
	 - [x] [Reverse Entries](#reverse-list)
	 - [ ] Data files used for filtering
		 - [x] [entity_types](#entity-data)
			 - [x] [default tags](#default-entity-tags)
		 - [x] [functions](#function-data)
			 - [x] [default tags](#default-function-tags)
		 - [ ] [fluids](#fluid-data)
			 - [ ] [default tags](#default-fluid-tags)
		 - [ ] [blocks](#block-data)
			 - [ ] [default tags](#default-block-tags)
		 - [ ] [items](#item-data)
			 - [ ] [default tags](#default-item-tags)

# How To Use
Download both "main.py" and "tags.py" and put them in your chosen project root directory. Create a directory called "tags" (where your tags go) and create your files (files can be present in any subdirectory that does not have "." at the beginning of it). Copy the ".saved" directory into your root (you can delete any file that doesn't begin with "minecraft" in ".saved/tags") In your "main.mcscript" file (create one if you don't have it; must be in root directory), add the following line to specify your pack details:

    pack-info: "[Pack name]" "[Pack ID (used for namespace)]" "[Pack description]" [Use snapshots (true or false)];

Run the "main.py" file using python 3.8.2 (the version this was developed in), and your data pack will be created in ".generated/packs/{pack_name}". You can copy-paste the entire folder to your world's data pack directory and your data pack should load without problems (unless you have a syntax error in one of your literal commands).

Currently, only tags will be generated based on input, while the functions will be populated by generic statements.

# Define a Tag
You may define a tag by creating a file with the "mctag" extension in the directory "./tags" relative to the main directory (the directory where you put "main.py" and "tags.py"). All subdirectories of "./tags" will be checked for files, and the resulting data pack will preserve subdirectories (so if you put a file in the "internal" folder, the tag name will be "#internal/[tag_name]").

On the first line of your file, you should specify the type of tag you are creating. Offically, you can create these tag types in data packs:

 - blocks
 - items
 - entity_types
 - fluids
 - functions

Defining the type ensures that the correct data file is used for filtering and that the tag is put in the correct directory of the data pack.

Each subsequent line of the file defines the entries you are placing in your tag and must be prefixed by either "+" or "-" unless it's a comment or one of the special operation functions (sort, limit, and reverse). All whitespace is ignored in every line.

Comment lines are ignored by the generator and may be prefixed by "#". You may also add a comment to the end of a line using the same character.

Format example:

    type: entity_types
    #This is a comment.
    + minecraft:armor_stand #This is also a comment.

There is an alternate way to define tags that can be used if you have a list of all entries that should be included. You may insert a "txt" file in the directory "./.saved/tags/[type]" that contains either a line separated or comma separated list of the specific entries that should be included (default namespace is "minecraft"). You may not specify other tags or filter entries - This format only accepts literal entry specifications.

Format example:

    minecraft:armor_stand
    minecraft:potion

# Add Entries
You may add an entry to your tag using a line that starts with "+". You have multiple choices for how to determine which entries to add. The most basic option is to specify the name of an entry such as "minecraft:arrow". If you would like, you may omit the namespace and "minecraft:" will automatically be prepended to your entry.

Format Example:

    + minecraft:arrow
    + armor_stand
 
# Remove Entries
You may remove entries from a tag in a similar way that you [add entries](#add-entries) to it, just with a "-" at the beginning of the line instead of a "+". Anything that can be added can also be removed.

Format Example:

    - minecraft:arrow
    - armor_stand
    
# Tag Comments
A comment is used by the programmer to communicate stuff about their code, but it is not used in any way by the interpreter and will not appear anywhere in the generated pack. Lines that begin with "#" are considered comments. You may also trail a line with "#{text}..." and that will be considered a comment as well.

Format Example:

    #This is a comment
    + minecraft:arrow
    + armor_stand #This is also a comment
    
# Specify Other Tags
You may specify another tag instead of a literal entry when adding or subtracting. When you do so, the operation will be performed on each entry defined in the tag in the order in which they appear. The tags that Minecraft includes by default are all included as txt files (WIP). If you would like to specify your own, you must either create an mctag file or export it to the "tags/{type}" folder as text. Tags that are not found in the generator are appended as literals when generated in the datapack.

To specify another tag, use "all(#{path-to-tag})". You may also specify all entries that are *not* part of a tag using "all(!#{path-to-tag})"

Format example:

    + all(#minecraft:arrows)
    #All entries that are unused in the game
    + all(!#used)
 
# All
You may specify all available entries using  the word "all". This will look in the csv file specified as the type of the tag and append every entry found.

Format Example:

    type: items
    #Add Every item the generator knows of
    + all
 
# Filter By Name
You may add entries based on their name by adding arguments to the "all" function. The full syntax is "all({args})" where "args" is a list of arguments separated by commas. To specify that the name must contain a segment you may specify a single argument "{segment}" or (if you would like to use other arguments as well) you can specify "in={segment}" Only entries containing the specified segment will be added or removed.

You may also specify anything that *doesn't* contain the segment in the single argument "!{segment}" or "notin={segment}"

Format Example:

    #Add all entries containing "ball"
    + all(ball)
    # Remove all entries not containing "fire"
    - all(!fire)
  
# Filter by value
The generator not only stores a list of all valid entries, it also stores certain data about those entries, such as the height of each entity (WIP). You may use these to filter your values in a more detailed manner.

To specify that a key must be equal to a value, use the argument "{key}=={value}". You may also specify that a key must not equal a value using "{key}!={value}". You can specify, less than, grater than, less than or equal to, or greater than or equal to using "<", ">", "<=", and ">=" respectively.

Format Example:

    #Add all entries with the namespace "minecraft" that are taller than 1 block
    + all(namespace=="minecraft",height>1)
    
# Sort
The "all" function has an option to sort your entries either alphabetically or by a certain value instead of in the order it is seen. To use it, use the argument "sort=alphabetical" or "sort={key}". The first will sort alphabetically by name, while the second will sort based on the value of the key of each entry. Entries that are not found in the file are sorted alphabetically before entries that are, and entries that have integer values are sorted before entries with string values (which are sorted alphabetically by value).

Alternatively, you can sort an entire tag using the "sort" function that does not require a "+" or "-" at the beginning of the line. The syntax is either "sort(alphabetical)" or "sort(key)".

Format Example:

    + all(sort=height) #Add all sorted by height
    sort(alphabetical) #Sort the entire tag alphabetically

# Limit Count
You may limit the number of entries a function receives using either the "limit" argument or (to limit the entire tag) the "limit" function. The syntax for the argument is "limit={number}" and the function is "limit({number})". The number should be an integer. This will splice the list so that only the first {number} entries are included (so "limit=5" will only include the first 5 entries). If there are not that many entries, all entries will be included.

Format Example:

    + all(sort=height,limit=5) #The 5 entities with the lowest height
    limit(5) #Limit the length of this tag to 5
  
# Reverse List
You may specify to perform operations on the entries in reverse order or reverse the order of the entire tag. This is particularly useful for sorting things greatest to least rather than least to greatest. You may use the argument syntax "reverse={true or false}" or the function syntax "reverse".

Format Example:

    + all(sort=height,reverse=true) #All entries from tallest to shortest
    reverse #Reverse the order of the entire tag
# Entity Data
The following information is stored for every entity in the ".saved/data/entity_types.csv" file:
|key|description|possible values|
|--|--|--|
|namespace|The namespace the entity is defined in|string, no spaces or ":"
|name|The name of the entry|string, no spaces
|category|The entity category this entity fits in.<br>Hostile entities attack targets on sight.<br>Passive entities do not attack.<br>Neutral entities attack under certain conditions.<br>Projectile entities are fired for attacking.<br>Utility entities are used as tools rather than living creatures.|neutral, hostile, passive, utility, or projectile
|subcategory|A subcategory for the entity (if any)<br>Arthropods are insects that are affected by the "bane of arthropods" enchantment.<br>Undead entities burn in daylight and are harmed by healing potions.<br>Illagers are used in raid events.|n/a, arthropod, undead, or illager
|width|The witdth of the entities hitbox in blocks|decimal number
|height|The height of the entities hitbox in blocks|decimal number
|length|The height of the entities hitbox in blocks (for most entities this is eqwual to the width)|decimal number
|volume|The total amount of space in blocks the entity takes up. Calculated using the formula "length * width * height"|decimal number
|health|The maximum amount of health points this entity can have. "n/a" for entities that do not have health.|n/a or integer
|environment|The preferred environment for this entity|land, air, or water
|dimension|The dimension(s) this entity may be found naturally.|all, none, overworld, nether, end, or overworld/nether

# Default Entity Tags
The following entity tags are implemented into Minecraft by default and provided in the ".saved/tags" directory of the generator:
|name|contents|
|--|--|
|arrows|arrow, spectral_arrow|
|beehive_inhabitors|bee|
|impact_projectiles|arrow, spectral_arrow, snowball, fireball, small_fireball, egg, trident, dragon_fireball, wither_skull|
|raiders|evoker, illusioner, pillager, ravager, vindicator, witch|
|skeletons|skeleton, stray, wither_skeleton|
|powder_snow_walkable_mobs‌|rabbit, endermite, silverfish|

# Function Data
Each function you create using mcscript files will be added to the ".saved/data/functions.csv" file. You can also define external functions to be included within your mcscript file using 'def {namespace}:{function name}" (WIP). The following information is stored:
|key|description|possible values
|--|--|--|
|namespace|The namespace the entry is defined in.|string, no spaces or ":"|
|name|The name of the function as well as the data pack path it is stored in.|string, no spaces|


# Default Function Tags
Minecraft doesn't implement functions by default, so there are no default tags for functions.