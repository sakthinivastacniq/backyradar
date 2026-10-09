import datetime as dt
from competitor_monitor import parse_feed,factor

def test_dates_and_links():
 now=dt.datetime(2026,10,9,tzinfo=dt.timezone.utc)
 xml='''<rss><channel><item><title>New sensor</title><link>https://example.com/valid</link><pubDate>Thu, 08 Oct 2026 12:00:00 GMT</pubDate></item><item><title>Future</title><link>https://example.com/future</link><pubDate>Fri, 09 Oct 2027 12:00:00 GMT</pubDate></item><item><title>Unsafe</title><link>javascript:alert(1)</link><pubDate>Thu, 08 Oct 2026 12:00:00 GMT</pubDate></item><item><title>Undated</title><link>https://example.com/unknown</link></item></channel></rss>'''
 result=parse_feed(xml,{'name':'Example'},now)
 assert len(result)==1 and result[0]['reviewed'] is False
 assert result[0]['date']=='2026-10-08'

def test_factor():
 assert factor('Company acquired by investor')=='Funding / ownership'
 assert factor('New CEO appointed')=='Management'
