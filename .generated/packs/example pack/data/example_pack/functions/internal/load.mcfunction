#This function is run when the datapack is loaded.



#variable description



scoreboard objectives add used_carrot_on_a used:carrot_on_a_stick
function example_pack:listeners/load/main/load-1
tellraw @a [{"text":"The pack "},{"text":"\"example pack\" ","color":"green","hoverEvent":{"action":"show_text","contents":[{"text":"example_pack\nExample pack used for debugging"}]}},{"text":"has been sucessfully (re)loaded."}]