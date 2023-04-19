# streamlit_app.py
from pandas.core.arrays.integer import Int64Dtype
from Prediction import pop_predict, genre_predict
import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from PIL import Image
import os
import numpy as np
path = os.getcwd()
print(path)

# Page config
st.set_page_config(page_icon=":musical_note:", page_title="SpotifyPlus", layout="wide")



# Create API client.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(credentials=credentials)

# Perform query.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
# @st.cache_data(ttl=600)
#@st.experimental_memo
@st.cache_data # it shows warning using experimental_memo

def run_query(query):
    query_job = client.query(query)
    rows_raw = query_job.result()
    # Convert to list of dicts. Required for st.cache_data to hash the return value.
    rows = [dict(row) for row in rows_raw]
    return rows


hide_default_format = """
       <style>
       #MainMenu {visibility: hidden; }
       footer {visibility: hidden;}
       </style>
       """
st.markdown(hide_default_format, unsafe_allow_html=True)


# DATA
track_rows = run_query('SELECT * FROM `snappy-boulder-378707.History.Tracks` ORDER BY popularity desc')
track_df = pd.DataFrame(track_rows)

# genre_rows = run_query('SELECT * FROM `snappy-boulder-378707.GenrePopularity.GenrePopularity`')
# genre_df = pd.DataFrame(genre_rows)
# genre_df['mean_popularity'] = genre_df['popularity'] / genre_df['total_tracks']
# genres = genre_df['genre'].unique()
# genres = run_query("SELECT column_name FROM `snappy-boulder-378707.History.INFORMATION_SCHEMA.COLUMNS` WHERE table_name = '{}'".format('TrackGenre'))[1:]
feature_pop = run_query("SELECT * FROM `snappy-boulder-378707.History.AudioFeatures` as a join `snappy-boulder-378707.History.Tracks` as b on a.id = b.id join `snappy-boulder-378707.History.TrackGenre` as c on b.id = c.track_id ORDER BY popularity desc")
feature_pop_df = pd.DataFrame(feature_pop)
feature_rows = run_query('SELECT * FROM `snappy-boulder-378707.History.AudioFeatures`')
feature_df = pd.DataFrame(feature_rows)
track_feature_df = pd.merge(feature_df, track_df, on="id", how="inner")
track_feature_df = track_feature_df.sort_values(by=['popularity'],ascending=False)

artist_rows = run_query('SELECT * FROM `snappy-boulder-378707.History.Artists` ORDER BY popularity desc')
artist_df = pd.DataFrame(artist_rows)

track_genre_rows = run_query('SELECT * FROM `snappy-boulder-378707.History.TrackGenre`')
track_genre_df = pd.DataFrame(track_genre_rows)
track_feature_genre_df = pd.merge(track_feature_df, track_genre_df, left_on="id", right_on = "track_id",how="inner")
track_feature_genre_df = track_feature_genre_df.sort_values(by=['popularity'],ascending=False)

feature_distribution = pd.DataFrame(run_query('SELECT * FROM snappy-boulder-378707.History.FeatureDistribution'))
#Newly Release
popularity_diff = pd.DataFrame(run_query('''
SELECT t1.name, t3.release_date, t1.popularity as current_popularity,
t2.popularity as future_popularity, (t2.popularity - t1.popularity) as popularity_diff
FROM `snappy-boulder-378707.NewReleases.NewTracks`  as t1
inner join snappy-boulder-378707.NewReleases.PopularityPrediction as t2
on t1.id = t2.id
inner join snappy-boulder-378707.NewReleases.NewAlbums as t3
on t1.album_id = t3.id
order by 5 desc'''))
genre_predicted = pd.DataFrame(run_query('SELECT * FROM snappy-boulder-378707.NewReleases.GenrePrediction'))
new_artists = pd.DataFrame(run_query('''SELECT name, followers, popularity 
FROM snappy-boulder-378707.NewReleases.Artists as t1
order by followers desc, popularity desc
limit 3'''))
#Filters
genres = list(track_genre_df.columns)[1:]
features = list(feature_df.columns)

#logo
spotify_logo = Image.open(f"{path}/spotify_logo.png")
# spotify_logo = Image.open("../spotify_logo.png")
color_palette = sns.color_palette("Paired").pop(2)


# page config

st.title("SpotifyPlus")

st.sidebar.image(spotify_logo, width = 150)

# pre-defined functions

def plot_config(fig, ax):
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    ax.spines['bottom'].set_color('white')
    ax.spines['top'].set_color('white')
    ax.spines['left'].set_color('white')
    ax.spines['right'].set_color('white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.title.set_color('white')
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    return fig, ax


# main content

page = st.sidebar.radio(
    "Select your interested page",
    ('Market Overview', 'Newly Released', 'User Prediction'))

st.markdown('''
            <style>
            .st-c7 {
                flex-shrink: 0;
                position: absolute;
                opacity: 0;
                cursor: pointer;
                height: 0;
                width: 0;
            }
            </style>
            ''', unsafe_allow_html=True)

col1, col, col2 = st.columns([1,2,1])
with col:
    placeholder = st.image("""https://pyxis.nymag.com/v1/imgs/3a3/b1f/2141226b8ab1ae07afe4b541ee0d2b0825-11-yic-pop-essay.rsocial.w1200.jpg""")

# tab - visualisation
# if page1 == True:
if page == 'Market Overview':
    placeholder.empty()
    c0 = st.container()
    
    with c0:
        st.header("1. Feature Analysis")
        feature_option = st.selectbox('Choose a feature to plot', ('Danceability', 'Energy', 'Loudness', 'Speechiness', 'Acousticness', 'Instrumentalness', 'Liveness', 'Valence','Tempo', 'Duration_ms'))
        
        fig, ax = plt.subplots(figsize=(15,7))

        sns.lineplot(x='year', y= feature_option.lower(), data=feature_distribution,color='#79C', linewidth=2.5)
        ax.set_xlabel('Year',fontsize = 14)
        ax.set_ylabel(feature_option,fontsize = 14)
        fig, ax = plot_config(fig, ax)
        st.pyplot(fig)
    
    c2 = st.container()
    
    with c2:
        col1, col2, col3, col4 = st.columns([1,4,1,4])
        with col1:
            st.subheader("Filter:")
        with col2:
            # genre_chosen = genres
            genre_chosen = st.multiselect("Choose genre types",genres)
        # with col3:
        #     time_chosen = st.date_input("Release time", datetime.datetime.now())
        with col4:
            pop_threshold = st.slider("maximum poplarity", 0, 100, 100)
            # st.header("Top Tracks Features")
    

# Tracks in terms of popularity (/danceability/energy/singer/team etc) in a genre - scatter plot - 2
# Singers in terms of popularity/followers/no. of trending songs in general/genre -3
    c3 = st.container()
    
    with c3:
        # col1 = st.columns([1])
        # with col1:
        #feature_option = st.selectbox('Choose a feature to plot', ('Popularity','Danceability', 'Energy', 'Loudness', 'Speechiness', 'Acousticness', 'Instrumentalness', 'Liveness', 'Valence','Tempo', 'Duration_ms','Available_Markets'))
        if not genre_chosen:
            genre_chosen = genres
        pop_filtered = feature_pop_df[feature_pop_df['popularity'] <= pop_threshold]
        pop_filtered['sum'] = pop_filtered[genre_chosen].sum(axis = 1)
        filtered = pop_filtered[pop_filtered['sum'] >=1][0:5]
        fig, ax = plt.subplots(figsize=(15,7))

        sns.barplot(y=filtered['popularity'][0:5], x=filtered['name'][0:5], width = 0.6, palette="Set2")
        ax.set_xlabel('Track',fontsize = 14)
        ax.set_ylabel('Popularity',fontsize = 14)
        fig, ax = plot_config(fig, ax)
        st.pyplot(fig)

    c4 = st.container()
    with c4:
        st.header("2. Top Singers Analysis")
        artist_pop_threshold = st.slider("maximum artist poplarity", 0, 100, 100)
        attribute_option = st.selectbox('Choose an attribute to plot', ('Popularity','Followers'))
        fig, ax = plt.subplots(figsize=(15,7))
        artist_df = artist_df[artist_df['popularity'] <= artist_pop_threshold]
        if len(artist_df) > 0: 
            sns.barplot(y=artist_df[attribute_option.lower()][:5], x=artist_df['name'][:5], width= 0.6, palette="Set2")
            ax.set_xlabel('Singer',fontsize = 14)
            ax.set_ylabel(attribute_option,fontsize = 14)
            fig, ax = plot_config(fig, ax)
            st.pyplot(fig)

# # Top Tracks Features in Genre
#     c4 = st.container()
#     with c4:
#         st.header("Top Tracks Features in Genre")
#         col1, col2, col3 = st.columns([4,1,6])
#         with col1:
#             genre_option = st.selectbox('Choose a genre', genres)
#             genre_feature_option = st.selectbox('Choose a feature', ('Popularity','Danceability', 'Energy', 'Loudness', 'Speechiness', 'Acousticness', 'Instrumentalness', 'Liveness', 'Valence','Tempo', 'Duration_ms','Available_Markets'))
        
#         with col3:
#             fig, ax = plt.subplots(figsize=(18,7))
#             filter_by_genre = track_feature_genre_df[track_feature_genre_df[genre_option] == 1]
#             sns.barplot(y=filter_by_genre[genre_feature_option.lower()][:5], x=filter_by_genre['name'][:5].apply(lambda x: x[:40]), width = 0.6,palette="Set2")
#             ax.set_title(genre_feature_option + ' of Top 5 Tracks in Genre ' + genre_option, fontsize = 20)
#             ax.set_xlabel('Track',fontsize = 14)
#             ax.set_ylabel(genre_feature_option,fontsize = 14)
#             fig, ax = plot_config(fig, ax)
#             st.pyplot(fig)




# tab - prediction
if page == 'Newly Released':
    placeholder.empty()
    c1 = st.container()
    with c1:
        st.title("Newly Released Track Overview")
        #visual
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Total New Tracks", value=len(popularity_diff['name'].unique()),  delta_color="inverse")
        with col2:
            predicted_mean = round(np.mean(popularity_diff.future_popularity.values),2)
            current_mean = round(np.mean(popularity_diff.current_popularity.values),2)
            st.metric(label="Predicted Popularity", value=predicted_mean, delta = f'{round(predicted_mean - current_mean,2)} Current Popularity {current_mean}',  delta_color="inverse")
        
        col3, col4 = st.columns(2)
        with col3:
            g = sns.catplot(y = 'Genre',kind="count",data = genre_predicted, palette="pastel")
            g.set_axis_labels("Count of Tracks ", "Predicted Genre")
            fig, ax = g.fig, g.ax
            fig, ax = plot_config(fig, ax)
            st.pyplot(fig)
        
        with col4:
            for i in range(len(new_artists)):
                st.subheader(f':green[{new_artists.iloc[i,0]}] hitting the market')
                col5, col6 = st.columns(2)
                with col5:
                    st.caption(f'Followers: _{new_artists.iloc[i,1]}_')
                with col6:
                    st.caption(f'Popularity: _{new_artists.iloc[i,2]}_')
                st.markdown("""-----------------------""") ##need to reduce this
    
    c2 = st.container()
    with c2:
        st.title("Newly Released Track Details")
        cm = sns.light_palette("green", as_cmap=True)   
        st.dataframe( popularity_diff.style.set_properties(subset=['name'], **{'width': '2px'}).background_gradient(cmap=cm, subset=['popularity_diff']).highlight_max(subset=['current_popularity','future_popularity','popularity_diff'], color='lightblue').set_caption('Newly Release Popularity Prediction Detail.'),
                     use_container_width=True)



                

if page == 'User Prediction':
    placeholder.empty()
    c1 = st.container()
    c2 = st.container()
    with c1:
        st.title('Track Popularity Predictor')
        # visual
        col1, col2, col3 = st.columns([3, 1, 7])
        with col1:
            # filters - genre
            chosen_genre = st.selectbox('Choose a genre to plot', genres)
            # filters - feature
            chosen_feature = st.selectbox("choose a feature to plot", features)
            # filter - plot type
            chosen_plot = st.selectbox("choose a plot type", ["histogram", "boxplot"])
        with col3:
            target_df = track_feature_genre_df[track_feature_genre_df[chosen_genre] == 1]
            fig, ax = plt.subplots(figsize=(18,7))
            if chosen_plot == "boxplot":
                sns.boxplot(x=target_df[chosen_feature], color="#1DB954",flierprops={'marker': 'o', 'markersize': 10, 'markerfacecolor': '#1DB954'})
            else:
                sns.histplot(target_df[chosen_feature], color="#1DB954")
            fig, ax = plot_config(fig, ax)
            st.pyplot(fig)
                
        st.divider()
        # col1, col, col2 = st.columns([1,2,1])
        # with col:
        #     st.image("""https://pyxis.nymag.com/v1/imgs/3a3/b1f/2141226b8ab1ae07afe4b541ee0d2b0825-11-yic-pop-essay.rsocial.w1200.jpg""")
        col1, col, col2 = st.columns([7,1,7])
        with col1:
            released_date = st.date_input('Released Date:',datetime.datetime.now())
            danceability = st.number_input('Danceability:', min_value=0.0, max_value=1.0)
            energy = st.number_input('Energy:', min_value=0.0, max_value=1.0)
            key = st.selectbox('Key:', range(0,12))
            loudness = st.number_input('Loudness:', min_value=-60.0, max_value=1.0)
            mode = st.selectbox('Mode:', [0,1])
            speechiness = st.number_input('Speechiness:', min_value=0.0, max_value=1.0)
            acousticness = 	st.number_input('Acousticness:', min_value=0.0, max_value=1.0)
            instrumentalness = 	st.number_input('Instrumentalness:', min_value=0.0, max_value=1.0)
        with col2:
            liveness = st.number_input('Liveness:', min_value=0.0, max_value=1.0)
            valence = st.number_input('Valence:', min_value=0.0, max_value=1.0)
            tempo = st.number_input('Tempo:', min_value=0.0, max_value=500.0)
            duration_ms = st.number_input('Duration (ms):', min_value=0.0, max_value=1.0 * 10**10)
            time_signature = st.selectbox('Time signature:', range(3,8))
            explicit = 	st.selectbox('Explicit:', range(0,2))
            available_markets = st.number_input('Available markets:', min_value=0, max_value=500)
            followers = st.number_input('Followers:', min_value=0, max_value=1 * 10**10)
            popularity_artist = st.number_input('Artist popularity:', min_value=0.0, max_value=100.0)

        popularity_vars = [released_date,danceability,energy,key,loudness,mode,speechiness,acousticness,instrumentalness,liveness,valence,tempo,duration_ms,time_signature,explicit,available_markets,followers,popularity_artist]
        genre_vars = [danceability,energy,key,loudness,mode,speechiness,acousticness,instrumentalness,liveness,valence,tempo,duration_ms,time_signature]
        if st.button('Predict'):
            #Popularity
            popularity = pop_predict(popularity_vars)
            st.success(f'The predicted popularity of the track is {popularity[0]:.2f}')
            col1, col, col2 = st.columns([2,5,2])
            with col:
                fig, ax = plt.subplots(figsize=(15,8))
                sns.kdeplot(data=track_feature_df, x="popularity",fill = True,alpha=0.5, color = '#4CC9F0')
                plt.axvline(popularity[0], color = 'orange',linewidth = 6)
                fig, ax = plot_config(fig, ax)
                st.pyplot(fig)
            
            #Genre
            genres = genre_predict(genre_vars)
            st.success(f'The predicted genre of the track is {genres}')

        
            