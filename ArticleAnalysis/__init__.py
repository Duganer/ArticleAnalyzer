"""
The flask application package.
"""

from flask import Flask
app = Flask(__name__)

import ArticleAnalysis.render
import ArticleAnalysis.alpha
