import re
from datetime import datetime


class Logcluster:
    def __init__(self, logTemplate="", Nid="N0"):  # N0 means no match
        self.logTemplate = logTemplate
        self.Nid = Nid


class Node:
    def __init__(self, childD=None, depth=0, digitOrtoken=None):
        if childD is None:
            childD = dict()
        self.childD = childD
        self.depth = depth
        self.digitOrtoken = digitOrtoken


class LogParser:
    def __init__(self, depth=4, maxChild=100, st=0.6):
        self.depth = depth - 2  # 8- 2 = 6
        self.st = st  # similarity threshold
        self.maxChild = maxChild

        self.splitregex = re.compile(r"(\s+|:|<\*>|,|=)")
        self.template_dict = dict()
        self.rootNode = Node()

    def preprocess(self, line):
        logmessageL = self.splitregex.split(line.strip())

        compile_rule = re.compile(
            r"\d+[\.]\d+[\.]\d+[\.]\d+"
        )  # only for IP Address: 45.125.247.158

        for index, item in enumerate(logmessageL):
            if str.isdigit(
                item
            ):  # True if all the characters are digits, otherwise False https://www.w3schools.com/python/ref_string_isdigit.asp
                logmessageL[index] = "<*>"  # replace to <*>
            if compile_rule.match(
                item
            ):  # https://docs.python.org/3/library/re.html#re.match
                logmessageL[index] = "<*>"

        val = list(filter(lambda x: x != "", logmessageL))  # remove the empty items ''
        return val  # if line has 'eth0:7, 63.126.79.80#53' -> eth0:<*>, <*>'

    def parse(self, log_dataframe):  # Get templates with contents
        def getTemplate(seq1, seq2):
            assert len(seq1) == len(seq2)
            retVal = []
            for n, word in enumerate(seq2):
                if word == seq1[n]:
                    retVal.append(word)
                else:
                    retVal.append("<*>")
            return retVal

        def addSeqToPrefixTree(
            rn, logClust
        ):  # new clsuter calls this: rootNode, newCluster
            def hasNumbers(s):
                return any(char.isdigit() for char in s)

            def insert(parent, token, currentDepth):
                newNode = Node(depth=currentDepth + 1, digitOrtoken=token)
                parent.childD[token] = newNode
                return newNode

            seqLen = len(logClust.logTemplate)
            if seqLen not in rn.childD:
                firtLayerNode = Node(depth=1, digitOrtoken=seqLen)
                rn.childD[seqLen] = firtLayerNode
            else:
                firtLayerNode = rn.childD[seqLen]

            parentn = firtLayerNode

            currentDepth = 1
            for token in logClust.logTemplate:
                # Add current log cluster to the leaf node
                if currentDepth >= self.depth or currentDepth >= seqLen:
                    if len(parentn.childD) == 0:
                        parentn.childD = [logClust]
                    else:
                        parentn.childD.append(logClust)
                    break

                # If token not matched in this layer of existing tree.
                if token not in parentn.childD:
                    if (
                        not hasNumbers(token)
                        and len(parentn.childD) + 1 < self.maxChild
                    ):
                        parentn = insert(parentn, token, currentDepth)
                    else:
                        if "<*>" in parentn.childD:
                            parentn = parentn.childD["<*>"]
                        else:
                            parentn = insert(parentn, "<*>", currentDepth)
                # If the token is matched
                else:
                    parentn = parentn.childD[token]

                currentDepth += 1  # end of addSeqToPrefixTree

        # Parse
        print("Parsing dataframe")
        start_time = datetime.now()

        rootNode = self.rootNode
        logCluL = []

        for idx, line in log_dataframe.iterrows():
            logmessageL = self.preprocess(line["Content"])
            matchCluster = self.treeSearch(
                rootNode, logmessageL
            )  # matchCluster has id and template
            matchNid = ""

            if matchCluster is None:  # Match no existing log cluster
                Nid = "N" + str(len(logCluL) + 1)
                matchNid = Nid
                newCluster = Logcluster(logTemplate=logmessageL, Nid=Nid)
                logCluL.append(newCluster)
                addSeqToPrefixTree(rootNode, newCluster)
            else:  # Add the new log message to the existing cluster
                matchNid = matchCluster.Nid
                newTemplate = getTemplate(logmessageL, matchCluster.logTemplate)
                if "".join(newTemplate) != "".join(matchCluster.logTemplate):
                    matchCluster.logTemplate = newTemplate

        template_mapping = (
            dict()
        )  # {'E1': 'LDAP: SSL support unavailable', 'E2': 'suEXEC mechanism enabled (wrapper: /usr/sbin/suexec)' ...}
        for t in logCluL:
            template = "".join(t.logTemplate)
            self.template_dict[t.Nid] = t.logTemplate
            template_mapping[t.Nid] = template

        print(
            "Created a Parse Tree with Samples. [Time taken: {!s}]".format(
                datetime.now() - start_time
            )
        )

        return template_mapping, self.rootNode

    def treeSearch(
        self, rn, seq
    ):  # rootNode, logmessageL = tokens (no empty'', but including space ' ')
        def fastMatch(logClustL, seq):
            def seqDist(seq1, seq2):
                assert len(seq1) == len(seq2)
                simTokens = 0
                numOfPar = 0
                for token1, token2 in zip(seq1, seq2):
                    if token1 == "<*>":
                        numOfPar += 1
                        continue
                    if token1 == token2:
                        if (
                            token1 == "\t"
                            or token1.isspace()
                            or token1 == ":"
                            or token1 == ","
                            or token1 == "="
                            or token1 == "\n"
                        ):
                            continue
                        simTokens += 1
                        continue
                    if (
                        token1 == "\t"
                        or token1.isspace()
                        or token1 == ":"
                        or token1 == ","
                        or token1 == "="
                        or token1 == "\n"
                    ):
                        return -1, 0
                retVal = float(simTokens) / len(seq1)
                return retVal, numOfPar  # end of seqDist

            # fastMatch
            retLogClust = None
            maxSim = -2
            maxNumOfPara = -1
            maxClust = None
            for logClust in logClustL:
                curSim, curNumOfPara = seqDist(logClust.logTemplate, seq)
                if curSim > maxSim or (
                    curSim == maxSim and curNumOfPara > maxNumOfPara
                ):
                    maxSim = curSim
                    maxNumOfPara = curNumOfPara
                    maxClust = logClust
            if maxSim >= self.st:
                retLogClust = maxClust
            return retLogClust  # end of fastMatch

        # treeSearch
        retLogClust = None
        seqLen = len(seq)
        if seqLen not in rn.childD:
            return retLogClust

        parentn = rn.childD[seqLen]
        nodeStack = []
        nodeStack.append(parentn)

        while nodeStack:
            tempnode = nodeStack.pop()
            tempdepth = tempnode.depth
            if tempdepth >= self.depth or tempdepth >= seqLen:
                retLogClust = fastMatch(tempnode.childD, seq)
                if retLogClust:
                    return retLogClust
                continue
            if seq[tempdepth - 1] in tempnode.childD:
                nodeStack.append(tempnode.childD[seq[tempdepth - 1]])
                continue
            if "<*>" in tempnode.childD:
                nodeStack.append(tempnode.childD["<*>"])
        return retLogClust  # end of treeSearch

    def matchapply(self, line, nid):
        def get_parameter(logmessageL, template):
            ParameterList = []
            i = 0
            for token in template:
                if token == "<*>":
                    ParameterList.append(logmessageL[i])
                i += 1
            return ParameterList

        logmessageL = self.splitregex.split(line.strip())
        logmessageL = list(
            filter(lambda x: x != "", logmessageL)
        )  # remove the empty items
        assert len(logmessageL) == len(self.template_dict[nid])
        return nid, get_parameter(logmessageL, self.template_dict[nid])

    def match(self, log_dataframe, event):  # return a list of dataframe, sorted by Nid
        print("Matching All Dataframe")
        start_time = datetime.now()
        self.state = "Match"

        length = len(log_dataframe)

        log_dataframe["EventId"] = event
        s = log_dataframe.apply(
            lambda x: self.matchapply(x["Content"], x["EventId"]), axis=1
        )
        log_dataframe["ParameterList"] = s.apply(lambda s: s[1])

        print("Matching done. [Time taken: {!s}]".format(datetime.now() - start_time))
        print(log_dataframe)

    def get_parameter_list(self, content, template_regex):
        # template_regex = re.sub(r"<.{1,5}>", "<*>", template)
        if "<*>" not in template_regex:
            return []

        if "\s" in template_regex:  # some line has \s due to a double space
            template_regex = template_regex.replace("\s", "")  # replace

        if "\s" in content:
            content = content.replace("\s", "")

        template_regex = re.sub(r"([^A-Za-z0-9])", r"\\\1", template_regex)
        template_regex = re.sub(r"\\ +", r"\\s+", template_regex)
        template_regex = "^" + template_regex.replace("\<\*\>", "(.*?)") + "$"
        parameter_list = re.findall(template_regex, content)
        parameter_list = parameter_list[0] if parameter_list else ()
        parameter_list = (
            list(parameter_list)
            if isinstance(parameter_list, tuple)
            else [parameter_list]
        )
        return parameter_list
