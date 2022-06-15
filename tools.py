import re


def isUnescaped(string, index, escapeChar):
    if index < 0:
        index = len(string) + index
    ind = re.escape(string[index])
    regex = f"(?:(?<!{escapeChar})(?:{escapeChar}(?:{escapeChar}(?:{escapeChar}{{2}})*))?)({ind})"
    for match in re.finditer(regex, string[:index + 1]):
        if match.start(1) == index:
            return True
    return False


def isEscaped(string, index, escapeChar):
    if index < 0:
        index = len(string) + index
    ind = re.escape(string[index])
    regex = f"(?:(?<!{escapeChar})(?:{escapeChar}(?:{escapeChar}{{2}})*))({ind})"
    for match in re.finditer(regex, string[:index + 1]):
        if match.start(1) == index:
            return True
    return False


"""
Given a list of lists (or ranges) [li], return if [x] is included in any of them
"""


def inAny(x, li):
    for i in li:
        if x in i:
            return True

    return False


def segment(s, i, string):
    for ind in range(0, len(s)):
        if not s[ind] == string[ind + i]:
            return False

    return True


"""
A method used in parsing to determine which indexes that are surrounded in a given list of value pairs.
For example, if the ignoreChars value was [["(",")"]] and the string was "(hello (guys)) (hi)", this method
would identify the range including "(hello (guys))", enabling methods to consider that one element rather than
multiple.

Each item in the ignoreChars parameter is a pair of start and end values. Defining multiple items will add alternative
pairs. You may optionally provide a third argument that is a boolean defining whether the pair characters may be escaped.
"""


def ignoreIndexes(string, ignoreChars, inclusive, escapeChar=r"\\"):
    altInds = []
    if (len(ignoreChars) > 1):
        for i in ignoreChars:
            altInds.extend(
                ignoreIndexes(string, [i], False, escapeChar=escapeChar))

    result = []
    ignore = False
    ignoreCount = 0
    ignoreList = None
    startIndex = -1

    for i in range(0, len(string)):
        if (not ignoreList == None
        ) and len(ignoreList) > 2 and ignoreList[2] == True and isEscaped(
            string, i, escapeChar):
            # The character is escaped. Continue as if it wasn't there.
            continue

        c = string[i]
        if not ignore:
            for l in ignoreChars:
                if c == l[0] and not inAny(i, altInds):
                    ignoreList = l
                    ignoreCount += 1
                    ignore = True
                    startIndex = i
        elif not ignoreList[0] == ignoreList[1]:
            if ignoreList[0] == c and not inAny(i, altInds):
                ignoreCount += 1

            if ignoreList[1] == c and not inAny(i, altInds):
                ignoreCount -= 1
                if ignoreCount == 0:
                    ignoreList = None
                    ignore = False
                    result.append(
                        range(startIndex + int(not inclusive),
                              i + int(inclusive)))
                    startIndex = -1
        elif ignoreList[1] == c and not inAny(i, altInds):
            ignoreCount = 0
            ignoreList = None
            ignore = False
            result.append(
                range(startIndex + int(not inclusive), i + int(inclusive)))
            startIndex = -1

    return result


"""
Get the strings associated with a specific call of ignoreIndexes
"""


def groups(string, ignoreChars, inclusive, requiredPair=None, escapeChar="\\"):
    result = []
    indexes = ignoreIndexes(
        string, ignoreChars, True, escapeChar=re.escape(escapeChar))
    for r in indexes:
        result.append(string[r[0]:r[-1] + 1])

    if requiredPair != None:
        for s in result:
            if not (s[0] == requiredPair[0] and s[-1] == requiredPair[1]):
                result.remove(s)

    if not inclusive:
        for i in range(0, len(result)):
            result[i] = result[i][1:-1]

    for i in range(0, len(result)):
        for ignoreChar in ignoreChars:
            if len(ignoreChar) > 2 and ignoreChar[2]:
                result[i] = result[i].replace(
                    f"{escapeChar}{ignoreChar[0]}",
                    f"{ignoreChar[0]}").replace(f"{escapeChar}{ignoreChar[1]}",
                                                f"{ignoreChar[1]}")
        result[i] = result[i].replace(escapeChar * 2, escapeChar)

    return result


"""
Return the first appearance of {character} in {string} that is not part of a group defined by {ignoreChars}
(see ignoreIndexes)
"""


def indexOf(character, string, ignoreChars, escapeChar="\\"):
    ignoreInds = ignoreIndexes(
        string, ignoreChars, True, escapeChar=re.escape(escapeChar))

    for i in range(0, len(string)):
        c = string[i]
        if (not inAny(i, ignoreInds)) and c == character:
            return i

    # No match was found
    return -1


"""
Takes a list of file lines as {data} and removes any comments. That is, any lines
that start with "#" and any characters that trail after "#" at the end of a line.
"""


def noComments(data):
    result = []

    for l in data:
        line = l.strip()
        hashtagIndex = indexOf(
            "#", line, [["\"", "\""], ["[", "]"], ["/", ";"], ["(", ")"]])
        if hashtagIndex > 0:
            result.append(line[:hashtagIndex].strip())
        elif hashtagIndex != 0 and len(line) > 0:
            result.append(line)

    return result


"""
Return a list of elements separated by {separator} in {string}, grouping using the {ignoreChars}
(see ignoreIndexes)
"""


def words(separator,
          string,
          ignoreChars,
          separatorInclusive,
          ignoreCharInclusive,
          escapeChar="\\"):
    result = [""]
    ignoreInds = ignoreIndexes(
        string, ignoreChars, True, escapeChar=re.escape(escapeChar))
    skip = 0

    for i in range(0, len(string)):
        if skip > 0:
            skip -= 1
        else:
            if (not inAny(i, ignoreInds)) and segment(separator, i, string):
                if separatorInclusive:
                    result[-1] += separator
                result.append("")
                skip = len(separator) - 1
            elif ignoreCharInclusive or not (
                    i >= 2 and inAny(string[i], ignoreChars)
                    and isUnescaped(string, i, re.escape(escapeChar))):
                result[-1] += string[i]

    if result[-1] == "":
        result = result[:len(result) - 1]

    for i in range(0, len(result)):
        for ignoreChar in ignoreChars:
            if len(ignoreChar) > 2 and ignoreChar[2]:
                result[i] = result[i].replace(
                    f"{escapeChar}{ignoreChar[0]}",
                    f"{ignoreChar[0]}").replace(f"{escapeChar}{ignoreChar[1]}",
                                                f"{ignoreChar[1]}")
        result[i] = result[i].replace(escapeChar * 2, escapeChar)

    return result
