from bknet.src import run_system
from bknet.kis.tr_rest import KisHttpClient

import orjson

async def main():

    with open('tests/kis_config.yaml', 'r') as f:
        import yaml
        config = yaml.safe_load(f)

    httpClient = await KisHttpClient.New(
        appkey = config['kis']['dev']['api_key'],
        appsecret = config['kis']['dev']['api_secret'],
    )

    resp = await httpClient.kr_future_board('')
    nearby_kospi200_fut_code = [
        (fut['futs_shrn_iscd'], fut['hts_rmnn_dynu']) for fut in sorted([fut for fut in orjson.loads(resp.content)['output']], key=lambda x: int(x['hts_rmnn_dynu']))
    ][0]
    resp = await httpClient.kr_future_board('MKI')
    nearby_mini_kospi200_fut_code = [
        (fut['futs_shrn_iscd'], fut['hts_rmnn_dynu']) for fut in sorted([fut for fut in orjson.loads(resp.content)['output']], key=lambda x: int(x['hts_rmnn_dynu']))
    ][0]

    

if __name__ == "__main__":
    run_system(main())

