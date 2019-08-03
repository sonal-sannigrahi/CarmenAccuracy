#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 11 13:33:00 2019

@author: sonalsannigrahi
"""
########################### TWEET ATTRIBUTES ############################
# created_at, id, id_str, full_text, truncated, display_text_range,     #
# entities, source, in_reply_to_status_id, in_reply_to_status_id_str,   #
# in_reply_to_user_id, in_reply_to_user_id_str, in_reply_to_screen_name,#
# user, geo, coordinates, place, contributors, is_quote_status,         #
# retweet_count, favorite_count, favorited, retweeted, lang             #
#########################################################################

import json
import carmen 
import copy
import math
import reverse_geocoder as rgr
import numpy as np

#Need to run code twice to generate the first csv file.
#This is because the csv file is dependent on the Current.json
tweets = []

for i in range(1,15):
    n = str(i)
    name = str(i) + ".json"
    with open(name, "r") as file:
        for line in file.readlines():
            dictionary = json.loads(line)
            if len(dictionary) != 1:
                tweets.append(dictionary)

#The above creates a list of tweets with the following GEOBOX:
# GEOBOX_US = [-129.5,22.3,-65.8,51.18], which includes all of U.S., some parts
#of Canada and Mexico. 
                    
#"geo":{"type":"Point","coordinates":[35.8963318,-117.7021637]},"coordinates":{"type":"Point","coordinates":[-117.7021637,35.8963318]}

tweets_known = []
for tweet in tweets:
    if tweet['geo'] != None:
        tweets_known.append(tweet)

tweets_copy = copy.deepcopy(tweets_known)

#carmen copy set to "geo":null,"coordinates":null
for tweet in tweets_copy:
    tweet['geo'] = None
    tweet['coordinates'] =  None

#Geolocation using Carmen and JSON tweet for comparison
    
resolver = carmen.get_resolver()
resolver.load_locations()

locations = [] #initialised empt

for tweet in tweets_copy: #copy with geolocation removed
    location = resolver.resolve_tweet(tweet)
    if location != None:
        if location[0] == False:
            loc_dict = {}
            loc_dict['created at'] = str(tweet["created_at"])
            loc_dict['tweet id'] = str(tweet["id_str"]) 
            loc_dict['latitude match'] = location[1].latitude
            loc_dict['longitude match'] = location[1].longitude
            locations.append(loc_dict)
              
#create new json file of location, parsing through each entry of locations dictionary
final_file = open("carmen_guess.json","w+") 
for i in range(len(locations)):
    final_file.write(str(locations[i]) + '\n')
final_file.close() 

#Known geoloc 
    
locations_known = [] #initialised empt

for tweet in tweets_known: #copy with geolocation
    loc_dict = {}
    loc_dict['created at'] = str(tweet["created_at"])
    loc_dict['tweet id'] = str(tweet["id_str"]) 
    loc_dict['latitude match'] = tweet["coordinates"]["coordinates"][1]
    loc_dict['longitude match'] = tweet["coordinates"]["coordinates"][0]
    locations_known.append(loc_dict)
#create new json file of location, parsing through each entry of locations dictionary
final_file = open("carmen_known.json","w+") 
for j in range(len(locations_known)):
    final_file.write(str(locations_known[j]) + '\n')
final_file.close()


#Haversine Distance calculator

#Credit: Mahadev, Geeks for Geeks for Haversine Distance Calculator 

def haversine(lat1, lon1, lat2, lon2): 
      
    # distance between latitudes 
    # and longitudes 
    d_Lat = (lat2 - lat1) * math.pi / 180.0
    d_Lon = (lon2 - lon1) * math.pi / 180.0
  
    # convert input into radians
    lat1 = (lat1) * math.pi / 180.0
    lat2 = (lat2) * math.pi / 180.0
  
    # apply haversine formula 
    a = (pow(math.sin(d_Lat / 2), 2) + 
         pow(math.sin(d_Lon / 2), 2) * 
             math.cos(lat1) * math.cos(lat2));
    rad = 6371 #radius of the Earth in km
    c = 2 * math.asin(math.sqrt(a))  #apply inverse
    return rad * c 

#Euclidean Distance calculator 

def euc(lat1, lon1, lat2, lon2):
    #convert to 3-D point in space
    R = 6367 #radius of earth in km
    lat1 = (lat1) * math.pi / 180.0
    lat2 = (lat2) * math.pi / 180.0
    lon1 = (lon1) * math.pi / 180.0
    lon2 = (lon2) * math.pi / 180.0
    point_1 = np.array((R* math.cos(lat1)* math.cos(lon1), R*math.cos(lat1)*math.sin(lon1), R*math.sin(lat1)))
    point_2 = np.array((R* math.cos(lat2)* math.cos(lon2), R*math.cos(lat2)*math.sin(lon2), R*math.sin(lat2)))
    return (np.linalg.norm(point_1 - point_2))

#Difference computation and writing to .csv

col = 'tweet id, city, city carmen, city match, county, county carmen, county match, state, state carmen, state match, distance haversine, distance euclidean \n'
tweet_number = ''

accuracy_file = open("check.csv", "w")
accuracy_file.write(col)
tweet_ids = []

for i in range(1,len(locations_known)):
    tweet_ids.append(locations_known[i]['tweet id'])

county = 0
city = 0
state = 0
total = len(locations)-1
for i in range(1,len(locations)):
    row = ''
    #find index in known file
    city_match = False
    county_match = False
    state_match = False
    index = tweet_ids.index(locations[i]['tweet id'])
    lat_known = locations_known[index + 1]['latitude match']
    long_known= locations_known[index + 1]['longitude match']
    lat_match = locations[i]['latitude match']
    long_match = locations[i]['longitude match']
    city_carmen =  rgr.search([(lat_match, long_match)])[0]['name']
    city_known = rgr.search([(lat_known, long_known)])[0]['name']
    county_known  = rgr.search([(lat_known, long_known)])[0]['admin2']
    county_carmen = rgr.search([(lat_match, long_match)])[0]['admin2']
    state_known  = rgr.search([(lat_known, long_known)])[0]['admin1']
    state_carmen = rgr.search([(lat_match, long_match)])[0]['admin1']
    if city_carmen == city_known:
        city_match = True
        city +=1
    if county_carmen == county_known and county_carmen != '':
        county_match = True 
        county +=1
    if state_carmen == state_known and state_carmen != '':
        state_match = True
        state +=1
    #creates issues with writing to csv file
    if city_carmen == 'Washington, D.C.':
        city_carmen = 'Washington'
    if city_known == 'Washington, D.C.':
        city_known = 'Washington'
    if state_carmen == 'Washington, D.C.':
        state_carmen = 'Washington'
    if state_known == 'Washington, D.C.':
        state_known = 'Washington'
    if city_carmen == 'Westwood, Los Angeles':
        city_carmen = 'Westwood'
    if city_known == 'Westwood, Los Angeles':
        city_known = 'Westwood'
    dist_dif = haversine(locations[i]['latitude match'], locations[i]['longitude match'], locations_known[index + 1]['latitude match'],locations_known[index + 1]['longitude match'])
    dist_euc = euc(locations[i]['latitude match'], locations[i]['longitude match'], locations_known[index + 1]['latitude match'],locations_known[index + 1]['longitude match'])
    row += locations[i]['tweet id'] + ', ' + str(city_known) + ', ' + str(city_carmen) + ', ' + str(city_match)+ ', ' + str(county_known) + ', ' + str(county_carmen) + ', ' + str(county_match) + ', ' + str(state_known) + ', ' + str(state_carmen) + ', ' + str(state_match) + ', ' +   str(dist_dif) + ', ' + str(dist_euc) + ' \n'
    accuracy_file.write(row)

acc_county = 100*(county/total)
acc_city = 100*(city/total)
acc_state = 100*(state/total)

print("State Accuracy: %s" % acc_state + "%")
print("County Accuracy: %s" % acc_county + "%" )
print("City Accuracy: %s" % acc_city + "%")
  
accuracy_file.close()
