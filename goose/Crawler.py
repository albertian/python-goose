# -*- coding: utf-8 -*-
"""\
This is a python port of "Goose" orignialy licensed to Gravity.com
under one or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.

Python port was written by Xavier Grangier for Recrutae

Gravity.com licenses this file
to you under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import os
import glob
from copy import deepcopy
from goose.Article import Article
from goose.utils import URLHelper
from goose.extractors import StandardContentExtractor
from goose.cleaners import StandardDocumentCleaner
from goose.outputformatters import StandardOutputFormatter
from goose.parsers import Parser
from goose.images.UpgradedImageExtractor import UpgradedImageIExtractor
from goose.network import HtmlFetcher


class CrawlCandidate(object):

    def __init__(self, config, url, rawHTML):
        self.config = config
        self.url = url
        self.rawHTML = rawHTML


class Crawler(object):

    def __init__(self, config):
        self.config = config
        self.logPrefix = "crawler:"

    def crawl(self, crawlCandidate):
        article = Article()

        parseCandidate = URLHelper.getCleanedUrl(crawlCandidate.url)
        rawHtml = self.getHTML(crawlCandidate, parseCandidate)
        if rawHtml is None:
            return article
        doc = self.getDocument(parseCandidate.url, rawHtml)

        extractor = self.getExtractor()
        docCleaner = self.getDocCleaner()
        outputFormatter = self.getOutputFormatter()
        # article
        article.finalUrl = parseCandidate.url
        article.linkhash = parseCandidate.linkhash
        article.rawHtml = rawHtml
        article.doc = doc
        article.rawDoc = deepcopy(doc)
        article.title = extractor.getTitle(article)
        # TODO
        # article.publishDate = config.publishDateExtractor.extract(doc)
        # article.additionalData = config.getAdditionalDataExtractor.extract(doc)
        article.metaLang = extractor.getMetaLang(article)
        article.metaFavicon = extractor.getMetaFavicon(article)
        article.metaDescription = extractor.getMetaDescription(article)
        article.metaKeywords = extractor.getMetaKeywords(article)
        article.canonicalLink = extractor.getCanonicalLink(article)
        article.domain = extractor.getDomain(article.finalUrl)
        article.tags = extractor.extractTags(article)
        # # before we do any calcs on the body itself let's clean up the document
        #Parser.getText2(article.doc)
        article.doc = docCleaner.clean(article)
        Parser.getText2(article.doc)
        # big stuff
        article.topNode = extractor.calculateBestNodeBasedOnClustering(article)
        #Parser.getText2(article.topNode)
        #normal yet
        if article.topNode is not None:
            # TODO
            # movies and images
            # article.movies = extractor.extractVideos(article.topNode)
            if self.config.enableImageFetching:
                imageExtractor = self.getImageExtractor(article)
                article.topImage = imageExtractor.getBestImage(article.rawDoc, article.topNode)
            #Parser.getText3(article.topNode)
            #

            article.topNode = extractor.postExtractionCleanup(article.topNode)
            #Parser.getText3(article.topNode)
            article.cleanedArticleText = outputFormatter.getFormattedText(article)
            #Parser.getText3(outputFormatter.getTopNode())
            

        # cleanup tmp file
        self.releaseResources(article)
        #Parser.getText3(article.topNode)
        #Parser.getText2(article.doc)
        return article

    def getHTML(self, crawlCandidate, parsingCandidate):
        if crawlCandidate.rawHTML:
            return crawlCandidate.rawHTML
        else:
            # fetch HTML
            html = HtmlFetcher().getHtml(self.config, parsingCandidate.url)
            return html

    def getImageExtractor(self, article):
        httpClient = None
        return UpgradedImageIExtractor(httpClient, article, self.config)

    def getOutputFormatter(self):
        return StandardOutputFormatter(self.config)

    def getDocCleaner(self):
        return StandardDocumentCleaner()

    def getDocument(self, url, rawHtml):
        doc = Parser.fromstring(rawHtml)
        return doc

    def getExtractor(self):
        return StandardContentExtractor(self.config)

    def releaseResources(self, article):
        path = '%s/%s_*' % (self.config.localStoragePath, article.linkhash)
        for fname in glob.glob(path):
            try:
                os.remove(fname)
            except OSError:
                # TODO better log handeling
                pass
