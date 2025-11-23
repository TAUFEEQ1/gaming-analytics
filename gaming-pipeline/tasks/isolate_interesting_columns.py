import luigi

class IsolateColumnsTask(luigi.Task):
    """
    A Luigi Task to isolate interesting columns from player averages data.
    """
    def output(self):
        return luigi.LocalTarget('data/interesting_data.csv')
    
    def input(self):
        return luigi.LocalTarget('data/onlineCasino.csv')

    def run(self):
        import pandas as pd
        
        # Read the input CSV file
        df = pd.read_csv(self.input().path)
        # rename money to stake
        df['stake'] = df['money']
        # rename peopleWin to payout
        df['payout'] = df['peopleWin']
        # people win vs people lost.
        df['house_net'] = df['peopleWin'] - df['peopleLost']

        # Isolate interesting columns
        interesting_df = df[['ID', 'stake', 'payout', 'house_net','outpay', 'time']]
        
        # Save the interesting player averages to the output CSV file
        interesting_df.to_csv(self.output().path, index=False)

if __name__ == '__main__':
    luigi.run()