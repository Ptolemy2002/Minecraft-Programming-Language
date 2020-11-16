# Minecraft-Programming-Language

This is a project that, when finished, will allow for the creation of data packs and data pack tags through a simple programming language syntax that resembles object oriented languages such as Java. This is intended to be much more powerful and user friendly than typing a series of commands like you do in regular development. Here are the planned features (checked features are implemented, while unchecked are works in progress):

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
