#This function is run when the datapack is loaded.



#variable description



#Used for listener used:carrot_on_a_stick
scoreboard objectives add used_c_stick used:carrot_on_a_stick
function example_pack:listeners/load/main/load1
tellraw @a [{"text":"The pack "},{"text":"\"example pack\" ","color":"green","hoverEvent":{"action":"show_text","contents":[{"text":"example_pack\nExample pack used for debugging"}]}},{"text":"has been sucessfully (re)loaded."}]